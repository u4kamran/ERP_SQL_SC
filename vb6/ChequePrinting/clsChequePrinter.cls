VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
  Persistable = 0  'NotPersistable
  DataBindingBehavior = 0  'vbNone
  DataSourceBehavior = 0   'vbNone
  MTSTransactionMode = 0   'NotAnMTSObject
END
Attribute VB_Name = "clsChequePrinter"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
'===============================================================================
' Reusable cheque print engine — load layout, scale DPI, print/preview objects.
' UI-independent: draw target is either Printer or a PictureBox/Form Scale.
'===============================================================================
Option Explicit

Private m_Layout As clsLayoutManager
Private m_PrinterMgr As clsPrinterManager
Private m_Audit As clsChequeAudit
Private m_Data As clsChequeData
Private m_Words As clsAmountToWords

Private m_Copies As Long
Private m_PrinterName As String
Private m_LastError As String

Public Event Progress(ByVal sMessage As String)
Public Event ObjectPrinted(ByVal sObjectName As String)

Private Sub Class_Initialize()
    Set m_Layout = New clsLayoutManager
    Set m_PrinterMgr = New clsPrinterManager
    Set m_Audit = New clsChequeAudit
    Set m_Words = New clsAmountToWords
    m_Copies = 1
End Sub

Private Sub Class_Terminate()
    Set m_Layout = Nothing
    Set m_PrinterMgr = Nothing
    Set m_Audit = Nothing
    Set m_Data = Nothing
    Set m_Words = Nothing
End Sub

Public Property Get Layout() As clsLayoutManager
    Set Layout = m_Layout
End Property

Public Property Get PrinterManager() As clsPrinterManager
    Set PrinterManager = m_PrinterMgr
End Property

Public Property Get Audit() As clsChequeAudit
    Set Audit = m_Audit
End Property

Public Property Get ChequeData() As clsChequeData
    Set ChequeData = m_Data
End Property

Public Property Set ChequeData(ByVal d As clsChequeData)
    Set m_Data = d
End Property

Public Property Get Copies() As Long
    Copies = m_Copies
End Property

Public Property Let Copies(ByVal l As Long)
    If l < 1 Then l = 1
    If l > 99 Then l = 99
    m_Copies = l
End Property

Public Property Get PrinterName() As String
    PrinterName = m_PrinterName
End Property

Public Property Let PrinterName(ByVal s As String)
    m_PrinterName = s
End Property

Public Property Get LastError() As String
    LastError = m_LastError
End Property

Public Function LoadLayout(ByVal lLayoutID As Long) As Boolean
    On Error GoTo Fail
    LoadLayout = m_Layout.LoadLayout(lLayoutID)
    Exit Function
Fail:
    m_LastError = FriendlyChequeError(Err.Number, Err.Description)
    LoadLayout = False
End Function

Public Function PrepareFromVoucher(ByVal sVoucherNo As String, Optional ByVal lSerial As Long = 0, _
                                   Optional ByVal lDocType As Long = 0, Optional ByVal nFiscal As Integer = 0) As Boolean
    Dim sMsg As String
    Set m_Data = New clsChequeData
    If Not m_Data.LoadFromVoucher(sVoucherNo, lSerial, lDocType, nFiscal) Then
        m_LastError = FriendlyChequeError(CHQ_ERR_NO_DATA, "Unable to load voucher")
        PrepareFromVoucher = False
        Exit Function
    End If
    If Not m_Data.IsValid(sMsg) Then
        m_LastError = sMsg
        PrepareFromVoucher = False
        Exit Function
    End If
    If m_Data.LayoutID > 0 Then
        Call LoadLayout(m_Data.LayoutID)
    ElseIf m_Data.BankID > 0 Then
        m_Data.LayoutID = m_Layout.LoadDefaultLayoutForBank(m_Data.BankID)
    End If
    PrepareFromVoucher = (m_Layout.LayoutID > 0)
    If Not PrepareFromVoucher Then m_LastError = FriendlyChequeError(CHQ_ERR_LAYOUT_MISSING, "")
End Function

'-------------------------------------------------------------------------------
' Preview onto any object with CurrentX/CurrentY/Print/Line/Font (PictureBox)
' dblZoom: 0.5 / 0.75 / 1 / 1.5 / 2  etc.
'-------------------------------------------------------------------------------
Public Sub RenderToSurface(ByVal oSurface As Object, Optional ByVal dblZoom As Double = 1#, _
                           Optional ByVal bShowGrid As Boolean = False, Optional ByVal lPreviewDpi As Long = 96)
    Dim i As Long
    Dim o As clsLayoutObject
    Dim sText As String
    Dim xTw As Single, yTw As Single, wTw As Single, hTw As Single
    Dim scaleTw As Double
    
    On Error GoTo Fail
    If m_Data Is Nothing Then Err.Raise CHQ_ERR_NO_DATA, , "No cheque data"
    If m_Layout.LayoutID = 0 Then Err.Raise CHQ_ERR_LAYOUT_MISSING, , "No layout"
    If dblZoom <= 0 Then dblZoom = 1
    
    m_Data.EnsureAmountInWords
    scaleTw = dblZoom
    
    oSurface.Cls
    oSurface.ScaleMode = vbTwips
    
    ' Cheque boundary
    xTw = CSng(MmToTwips(m_Layout.LeftMargin) * scaleTw)
    yTw = CSng(MmToTwips(m_Layout.TopMargin) * scaleTw)
    wTw = CSng(MmToTwips(m_Layout.ChequeWidth) * scaleTw)
    hTw = CSng(MmToTwips(m_Layout.ChequeHeight) * scaleTw)
    oSurface.Line (xTw, yTw)-(xTw + wTw, yTw + hTw), RGB(180, 180, 180), B
    
    If bShowGrid Then Call DrawGrid(oSurface, xTw, yTw, wTw, hTw, scaleTw)
    
    For i = 0 To m_Layout.ObjectCount - 1
        Set o = m_Layout.LayoutObject(i)
        If o.Visible Then
            sText = ResolveObjectText(o)
            Call DrawObject(oSurface, o, sText, scaleTw, False)
            RaiseEvent ObjectPrinted(o.ObjectName)
        End If
    Next i
    Exit Sub
Fail:
    m_LastError = FriendlyChequeError(Err.Number, Err.Description)
End Sub

Public Function PrintCheque(Optional ByVal bForceReprint As Boolean = False) As Boolean
    Dim sMsg As String
    Dim bReprint As Boolean
    Dim iCopy As Long
    Dim i As Long
    Dim o As clsLayoutObject
    Dim sText As String
    Dim sBankPrinter As String
    
    On Error GoTo Fail
    
    Call m_Audit.EnsurePermission(CHQ_PERM_PRINT)
    
    If m_Data Is Nothing Then Err.Raise CHQ_ERR_NO_DATA, , "No data"
    If Not m_Data.IsValid(sMsg) Then Err.Raise CHQ_ERR_NO_DATA, , sMsg
    If m_Layout.LayoutID = 0 Then Err.Raise CHQ_ERR_LAYOUT_MISSING, , "Layout missing"
    
    bReprint = m_Data.AlreadyPrinted()
    If bReprint Then
        If Not bForceReprint Then
            Err.Raise CHQ_ERR_ALREADY_PRINTED, , "Already printed"
        End If
        Call m_Audit.EnsurePermission(CHQ_PERM_REPRINT)
    End If
    
    ' Resolve printer
    If Len(m_PrinterName) = 0 Then
        sBankPrinter = GetBankDefaultPrinter(m_Data.BankID)
        m_PrinterName = m_PrinterMgr.ResolvePrinter(chqPrinterLastUsed, sBankPrinter)
    End If
    If Not m_PrinterMgr.SetActivePrinter(m_PrinterName) Then
        Err.Raise CHQ_ERR_PRINTER, , "Wrong Printer: " & m_PrinterName
    End If
    If Not m_PrinterMgr.ValidatePrinterReady(m_PrinterName, sMsg) Then
        Err.Raise CHQ_ERR_PRINTER, , sMsg
    End If
    
    Call m_Layout.LoadCalibration(m_PrinterName, m_Layout.LayoutID)
    Call m_PrinterMgr.ApplyPaperSettings(m_Layout.PaperSizeName, m_Layout.PaperOrientation, _
                                         m_Layout.ChequeWidth + m_Layout.LeftMargin * 2, _
                                         m_Layout.ChequeHeight + m_Layout.TopMargin * 2)
    
    m_Data.EnsureAmountInWords
    RaiseEvent Progress("Printing cheque " & m_Data.ChequeNo)
    
    For iCopy = 1 To m_Copies
        For i = 0 To m_Layout.ObjectCount - 1
            Set o = m_Layout.LayoutObject(i)
            If o.Visible And o.ObjectCode <> CHQ_OBJ_MICR_IGNORE Then
                sText = ResolveObjectText(o)
                Call DrawObject(Printer, o, sText, 1#, True)
                RaiseEvent ObjectPrinted(o.ObjectName)
            End If
        Next i
        Printer.EndDoc
    Next iCopy
    
    Call m_Audit.UpsertRegister(m_Data, m_Layout.LayoutID, bReprint, m_PrinterName)
    m_Data.PrintCount = m_Data.PrintCount + 1
    m_Data.StatusCode = IIf(bReprint, CHQ_STATUS_REPRINTED, CHQ_STATUS_PRINTED)
    
    PrintCheque = True
    Exit Function
Fail:
    m_LastError = FriendlyChequeError(Err.Number, Err.Description)
    On Error Resume Next
    Printer.KillDoc
    PrintCheque = False
End Function

Public Function PrintTestPage() As Boolean
    Dim o As clsLayoutObject
    Dim i As Long
    On Error GoTo Fail
    Call m_Audit.EnsurePermission(CHQ_PERM_CALIBRATE)
    If Len(m_PrinterName) = 0 Then m_PrinterName = WindowsDefaultPrinterName()
    If Not m_PrinterMgr.SetActivePrinter(m_PrinterName) Then Err.Raise CHQ_ERR_PRINTER, , m_PrinterName
    Call m_Layout.LoadCalibration(m_PrinterName, m_Layout.LayoutID)
    
    Printer.Print "CHEQUE ALIGNMENT TEST — " & Format$(Now, "dd-mmm-yyyy hh:nn")
    Printer.Print "Printer: " & m_PrinterName
    Printer.Print "Layout: " & m_Layout.LayoutName
    Printer.Print "Offsets mm L/R/T/B: " & m_Layout.OffsetLeft & " / " & m_Layout.OffsetRight & " / " & m_Layout.OffsetTop & " / " & m_Layout.OffsetBottom
    Printer.Print ""
    
    For i = 0 To m_Layout.ObjectCount - 1
        Set o = m_Layout.LayoutObject(i)
        If o.Visible Then
            Call DrawObject(Printer, o, o.ObjectName & " [" & Format$(o.XPos, "0.0") & "," & Format$(o.YPos, "0.0") & "]", 1#, True)
        End If
    Next i
    ' Corner marks
    Printer.Line (MmToTwips(m_Layout.LeftMargin + m_Layout.OffsetLeft), MmToTwips(m_Layout.TopMargin + m_Layout.OffsetTop))- _
                 Step(MmToTwips(5), 0)
    Printer.Line (MmToTwips(m_Layout.LeftMargin + m_Layout.OffsetLeft), MmToTwips(m_Layout.TopMargin + m_Layout.OffsetTop))- _
                 Step(0, MmToTwips(5))
    Printer.EndDoc
    PrintTestPage = True
    Exit Function
Fail:
    m_LastError = FriendlyChequeError(Err.Number, Err.Description)
    PrintTestPage = False
End Function

Private Function GetBankDefaultPrinter(ByVal lBankID As Long) As String
    Dim rs As ADODB.Recordset
    On Error Resume Next
    Set rs = ChqOpenRs("SELECT DefaultPrinter FROM BANK_MASTER WHERE BankID=" & lBankID)
    If Not rs.EOF Then GetBankDefaultPrinter = NzStr(rs!DefaultPrinter)
    If Not rs Is Nothing Then If rs.State = adStateOpen Then rs.Close
End Function

Private Function ResolveObjectText(ByVal o As clsLayoutObject) As String
    Dim s As String
    Select Case o.ObjectCode
        Case CHQ_OBJ_PAYEE_NAME
            s = ApplyPayeeCase(m_Data.PayeeName, m_Layout.PayeeCaseMode)
            s = TruncatePayee(s, m_Layout.PayeeMaxLength)
        Case CHQ_OBJ_AMOUNT
            s = FormatChequeAmount(m_Data.Amount, m_Layout.AmountFormatCode, _
                                   IIf(Len(m_Layout.CurrencyPrefix) > 0, m_Layout.CurrencyPrefix, m_Data.CurrencyCode), _
                                   m_Layout.ShowCurrencyPrefix)
        Case CHQ_OBJ_AMOUNT_WORDS
            s = m_Data.AmountInWords
            If Len(s) = 0 Then s = m_Words.ToWords(m_Data.Amount, m_Data.CurrencyCode, True)
        Case CHQ_OBJ_CHEQUE_DATE
            s = FormatChequeDate(m_Data.ChequeDate, m_Layout.DateFormatCode)
        Case CHQ_OBJ_DATE_DD
            s = Format$(m_Data.ChequeDate, "dd")
        Case CHQ_OBJ_DATE_MM
            s = Format$(m_Data.ChequeDate, "mm")
        Case CHQ_OBJ_DATE_YYYY
            s = Format$(m_Data.ChequeDate, "yyyy")
        Case CHQ_OBJ_AC_PAYEE, CHQ_OBJ_BEARER, CHQ_OBJ_CUSTOM_TEXT
            s = o.DefaultText
        Case CHQ_OBJ_COMPANY_NAME
            s = m_Data.CompanyName
        Case CHQ_OBJ_VOUCHER_NO
            s = m_Data.VoucherNo
        Case CHQ_OBJ_NARRATION
            s = m_Data.Narration
        Case CHQ_OBJ_WATERMARK
            s = UCase$(m_Data.StatusCode)
            If s = "DRAFT" Or s = "PRINTED" Or s = "REPRINTED" Then s = o.DefaultText
        Case CHQ_OBJ_CROSS_MARK, CHQ_OBJ_SIGNATURE, CHQ_OBJ_MICR_IGNORE, CHQ_OBJ_LOGO, CHQ_OBJ_QR_CODE
            s = vbNullString
        Case Else
            If Len(o.DataField) > 0 Then
                s = ResolveDataField(o.DataField)
            Else
                s = o.DefaultText
            End If
    End Select
    ResolveObjectText = s
End Function

Private Function ResolveDataField(ByVal sField As String) As String
    Select Case UCase$(sField)
        Case "PAYEE", "AC_TITLE": ResolveDataField = m_Data.PayeeName
        Case "AMOUNT": ResolveDataField = CStr(m_Data.Amount)
        Case "VOUCHERNO", "VOUCHER_NO": ResolveDataField = m_Data.VoucherNo
        Case "CHEQUENO", "CHEQUE_NO": ResolveDataField = m_Data.ChequeNo
        Case "NARRATION": ResolveDataField = m_Data.Narration
        Case "BANKACCOUNT": ResolveDataField = m_Data.BankAccount
        Case "USER": ResolveDataField = m_Data.UserName
        Case "BRANCH": ResolveDataField = m_Data.BranchName
        Case Else: ResolveDataField = vbNullString
    End Select
End Function

Private Sub DrawObject(ByVal oSurf As Object, ByVal o As clsLayoutObject, ByVal sText As String, _
                       ByVal dblZoom As Double, ByVal bIsPrinter As Boolean)
    Dim x As Single, y As Single, w As Single, h As Single
    Dim sngSize As Single
    Dim bBold As Boolean
    
    x = CSng(MmToTwips(m_Layout.EffectiveX(o)) * dblZoom)
    y = CSng(MmToTwips(m_Layout.EffectiveY(o)) * dblZoom)
    w = CSng(MmToTwips(o.Width) * dblZoom)
    h = CSng(MmToTwips(o.Height) * dblZoom)
    
    ' Auto-center cheque on page (optional)
    If m_Layout.AutoCenter And bIsPrinter Then
        Dim pageW As Single, chqW As Single
        On Error Resume Next
        pageW = Printer.ScaleWidth
        chqW = CSng(MmToTwips(m_Layout.ChequeWidth + m_Layout.LeftMargin * 2))
        If pageW > chqW Then x = x + (pageW - chqW) / 2!
        On Error GoTo 0
    End If
    
    Select Case o.ObjectCode
        Case CHQ_OBJ_CROSS_MARK
            oSurf.DrawWidth = 1
            oSurf.Line (x, y)-(x + w, y + h), vbBlack
            oSurf.Line (x, y + h)-(x + w, y), vbBlack
            Exit Sub
        Case CHQ_OBJ_SIGNATURE
            oSurf.Line (x, y)-(x + w, y + h), RGB(200, 200, 200), B
            Exit Sub
        Case CHQ_OBJ_MICR_IGNORE
            If Not bIsPrinter Then
                oSurf.DrawStyle = vbDot
                oSurf.Line (x, y)-(x + w, y + h), RGB(220, 100, 100), B
                oSurf.DrawStyle = vbSolid
            End If
            Exit Sub
        Case CHQ_OBJ_LOGO, CHQ_OBJ_QR_CODE
            ' Reserved — place image via future enhancement
            If Not bIsPrinter Then oSurf.Line (x, y)-(x + w, y + h), RGB(150, 150, 220), B
            Exit Sub
    End Select
    
    If Len(sText) = 0 Then Exit Sub
    
    On Error Resume Next
    oSurf.FontName = o.FontName
    sngSize = CSng(o.FontSize)
    bBold = o.Bold
    oSurf.FontBold = bBold
    oSurf.FontItalic = o.Italic
    oSurf.FontSize = sngSize
    If o.ForeColor <> 0 Then oSurf.ForeColor = o.ForeColor Else oSurf.ForeColor = vbBlack
    
    ' Auto-shrink font to fit width
    If m_Layout.PayeeAutoShrink Or o.ObjectCode = CHQ_OBJ_PAYEE_NAME Or o.ObjectCode = CHQ_OBJ_AMOUNT_WORDS Then
        Do While oSurf.TextWidth(sText) > w And sngSize > o.MinFontSize And o.MinFontSize > 0
            sngSize = sngSize - 0.5!
            oSurf.FontSize = sngSize
        Loop
    End If
    
    ' Alignment within box
    Select Case o.Alignment
        Case chqAlignCenter
            oSurf.CurrentX = x + (w - oSurf.TextWidth(sText)) / 2!
        Case chqAlignRight
            oSurf.CurrentX = x + w - oSurf.TextWidth(sText)
        Case Else
            oSurf.CurrentX = x
    End Select
    oSurf.CurrentY = y + (h - oSurf.TextHeight(sText)) / 2!
    
    If m_Layout.PayeeWrap And o.ObjectCode = CHQ_OBJ_PAYEE_NAME Then
        Call PrintWrapped(oSurf, sText, x, y, w, h)
    Else
        ' Rotation: VB6 Printer has limited rotation; use Escape API in future.
        ' For 0 degrees, standard Print.
        If o.Rotation = 0 Then
            oSurf.Print sText
        Else
            oSurf.Print sText  ' fallback; designer stores rotation for future GDI+
        End If
    End If
    On Error GoTo 0
End Sub

Private Sub PrintWrapped(ByVal oSurf As Object, ByVal sText As String, _
                         ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single)
    Dim words() As String
    Dim i As Long
    Dim line As String
    Dim test As String
    Dim cy As Single
    words = Split(sText, " ")
    cy = y
    line = ""
    For i = LBound(words) To UBound(words)
        test = Trim$(line & " " & words(i))
        If oSurf.TextWidth(test) > w And Len(line) > 0 Then
            oSurf.CurrentX = x
            oSurf.CurrentY = cy
            oSurf.Print line
            cy = cy + oSurf.TextHeight("Ag")
            If cy > y + h Then Exit Sub
            line = words(i)
        Else
            line = test
        End If
    Next i
    If Len(line) > 0 Then
        oSurf.CurrentX = x
        oSurf.CurrentY = cy
        oSurf.Print line
    End If
End Sub

Private Sub DrawGrid(ByVal oSurf As Object, ByVal x As Single, ByVal y As Single, _
                     ByVal w As Single, ByVal h As Single, ByVal dblZoom As Double)
    Dim gx As Single, gy As Single
    Dim stepTw As Single
    stepTw = CSng(MmToTwips(5) * dblZoom) ' 5mm grid
    oSurf.DrawStyle = vbDot
    gx = x
    Do While gx <= x + w
        oSurf.Line (gx, y)-(gx, y + h), RGB(230, 230, 230)
        gx = gx + stepTw
    Loop
    gy = y
    Do While gy <= y + h
        oSurf.Line (x, gy)-(x + w, gy), RGB(230, 230, 230)
        gy = gy + stepTw
    Loop
    oSurf.DrawStyle = vbSolid
End Sub
