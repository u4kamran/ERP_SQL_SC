VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
  Persistable = 0  'NotPersistable
  DataBindingBehavior = 0  'vbNone
  DataSourceBehavior = 0   'vbNone
  MTSTransactionMode = 0   'NotAnMTSObject
END
Attribute VB_Name = "clsLayoutManager"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
'===============================================================================
' Load / cache / save cheque layouts. Coordinates cached in memory for session.
'===============================================================================
Option Explicit

Private Type tLayoutHeader
    LayoutID As Long
    BankID As Long
    LayoutName As String
    ChequeWidth As Double
    ChequeHeight As Double
    TopMargin As Double
    LeftMargin As Double
    PrinterDPI As Long
    PaperOrientation As eChqOrientation
    PaperSizeName As String
    DateFormatCode As String
    AmountFormatCode As String
    CurrencyPrefix As String
    ShowCurrencyPrefix As Boolean
    PayeeCaseMode As eChqPayeeCase
    PayeeMaxLength As Long
    PayeeWrap As Boolean
    PayeeAutoShrink As Boolean
    AutoCenter As Boolean
    Active As Boolean
End Type

' NOTE: VB6 does not allow class/object members inside a UDT.
' Cache entries are clsLayoutCacheEntry objects held in a Collection.
Private m_Cache As Collection

Private m_Current As tLayoutHeader
Private m_Objects() As clsLayoutObject
Private m_ObjectCount As Long
Private m_Loaded As Boolean

' Calibration offsets (mm)
Public OffsetLeft As Double
Public OffsetRight As Double
Public OffsetTop As Double
Public OffsetBottom As Double

Private Sub Class_Initialize()
    Set m_Cache = New Collection
End Sub

Private Sub Class_Terminate()
    Set m_Cache = Nothing
End Sub

Public Property Get LayoutID() As Long
    LayoutID = m_Current.LayoutID
End Property

Public Property Get BankID() As Long
    BankID = m_Current.BankID
End Property

Public Property Get LayoutName() As String
    LayoutName = m_Current.LayoutName
End Property

Public Property Get ChequeWidth() As Double
    ChequeWidth = m_Current.ChequeWidth
End Property

Public Property Get ChequeHeight() As Double
    ChequeHeight = m_Current.ChequeHeight
End Property

Public Property Get TopMargin() As Double
    TopMargin = m_Current.TopMargin
End Property

Public Property Get LeftMargin() As Double
    LeftMargin = m_Current.LeftMargin
End Property

Public Property Get PrinterDPI() As Long
    PrinterDPI = m_Current.PrinterDPI
End Property

Public Property Get PaperOrientation() As eChqOrientation
    PaperOrientation = m_Current.PaperOrientation
End Property

Public Property Get PaperSizeName() As String
    PaperSizeName = m_Current.PaperSizeName
End Property

Public Property Get DateFormatCode() As String
    DateFormatCode = m_Current.DateFormatCode
End Property

Public Property Get AmountFormatCode() As String
    AmountFormatCode = m_Current.AmountFormatCode
End Property

Public Property Get CurrencyPrefix() As String
    CurrencyPrefix = m_Current.CurrencyPrefix
End Property

Public Property Get ShowCurrencyPrefix() As Boolean
    ShowCurrencyPrefix = m_Current.ShowCurrencyPrefix
End Property

Public Property Get PayeeCaseMode() As eChqPayeeCase
    PayeeCaseMode = m_Current.PayeeCaseMode
End Property

Public Property Get PayeeMaxLength() As Long
    PayeeMaxLength = m_Current.PayeeMaxLength
End Property

Public Property Get PayeeWrap() As Boolean
    PayeeWrap = m_Current.PayeeWrap
End Property

Public Property Get PayeeAutoShrink() As Boolean
    PayeeAutoShrink = m_Current.PayeeAutoShrink
End Property

Public Property Get AutoCenter() As Boolean
    AutoCenter = m_Current.AutoCenter
End Property

Public Property Get ObjectCount() As Long
    ObjectCount = m_ObjectCount
End Property

Public Property Get LayoutObject(ByVal Index As Long) As clsLayoutObject
    If Index >= 0 And Index < m_ObjectCount Then
        Set LayoutObject = m_Objects(Index)
    End If
End Property

Public Sub ClearCache()
    Dim i As Long
    For i = m_Cache.Count To 1 Step -1
        m_Cache.Remove i
    Next i
End Sub

Public Function LoadLayout(ByVal lLayoutID As Long, Optional ByVal bForceReload As Boolean = False) As Boolean
    Dim i As Long
    Dim rs As ADODB.Recordset
    Dim sSql As String
    Dim o As clsLayoutObject
    Dim n As Long
    Dim entry As clsLayoutCacheEntry
    
    On Error GoTo Fail
    
    If Not bForceReload Then
        For i = 1 To m_Cache.Count
            Set entry = m_Cache(i)
            If entry.Loaded And entry.LayoutID = lLayoutID Then
                Call ApplyCacheEntry(entry)
                LoadLayout = True
                Exit Function
            End If
        Next i
    End If
    
    sSql = "SELECT * FROM CHEQUE_LAYOUT_MASTER WHERE LayoutID=" & lLayoutID & " AND Active=1"
    Set rs = ChqOpenRs(sSql)
    If rs.EOF Then
        rs.Close
        Err.Raise CHQ_ERR_LAYOUT_MISSING, "clsLayoutManager", "LayoutID " & lLayoutID
    End If
    
    With m_Current
        .LayoutID = NzLng(rs!LayoutID)
        .BankID = NzLng(rs!BankID)
        .LayoutName = NzStr(rs!LayoutName)
        .ChequeWidth = NzDbl(rs!ChequeWidth)
        .ChequeHeight = NzDbl(rs!ChequeHeight)
        .TopMargin = NzDbl(rs!TopMargin)
        .LeftMargin = NzDbl(rs!LeftMargin)
        .PrinterDPI = NzLng(rs!PrinterDPI, 300)
        .PaperOrientation = NzLng(rs!PaperOrientation, chqLandscape)
        .PaperSizeName = NzStr(rs!PaperSizeName)
        .DateFormatCode = NzStr(rs!DateFormatCode)
        .AmountFormatCode = NzStr(rs!AmountFormatCode)
        .CurrencyPrefix = NzStr(rs!CurrencyPrefix)
        .ShowCurrencyPrefix = NzBool(rs!ShowCurrencyPrefix)
        .PayeeCaseMode = NzLng(rs!PayeeCaseMode, chqCaseUpper)
        .PayeeMaxLength = NzLng(rs!PayeeMaxLength)
        .PayeeWrap = NzBool(rs!PayeeWrap)
        .PayeeAutoShrink = NzBool(rs!PayeeAutoShrink, True)
        .AutoCenter = NzBool(rs!AutoCenter)
        .Active = NzBool(rs!Active, True)
    End With
    rs.Close
    
    sSql = "SELECT * FROM CHEQUE_LAYOUT_DETAIL WHERE LayoutID=" & lLayoutID & " ORDER BY PrintOrder, DetailID"
    Set rs = ChqOpenRs(sSql)
    n = 0
    If Not rs.EOF Then
        rs.MoveLast
        n = rs.RecordCount
        rs.MoveFirst
    End If
    If n > 0 Then
        ReDim m_Objects(0 To n - 1)
    Else
        Erase m_Objects
    End If
    m_ObjectCount = 0
    Do While Not rs.EOF
        Set o = New clsLayoutObject
        With o
            .DetailID = NzLng(rs!DetailID)
            .LayoutID = lLayoutID
            .ObjectName = NzStr(rs!ObjectName)
            .ObjectCode = UCase$(NzStr(rs!ObjectCode))
            .XPos = NzDbl(rs!XPos)
            .YPos = NzDbl(rs!YPos)
            .Width = NzDbl(rs!Width)
            .Height = NzDbl(rs!Height)
            .FontName = NzStr(rs!FontName)
            If Len(.FontName) = 0 Then .FontName = "Arial"
            .FontSize = NzDbl(rs!FontSize, 10)
            .Bold = NzBool(rs!Bold)
            .Italic = NzBool(rs!Italic)
            .Alignment = NzLng(rs!Alignment)
            .Visible = NzBool(rs!Visible, True)
            .Rotation = CInt(NzLng(rs!Rotation))
            .PrintOrder = NzLng(rs!PrintOrder, 100)
            .DefaultText = NzStr(rs!DefaultText)
            .ForeColor = NzLng(rs!ForeColor, 0)
            .LineStyle = NzLng(rs!LineStyle)
            .DataField = NzStr(rs!DataField)
            .MinFontSize = NzDbl(rs!MinFontSize, 7)
            If .Width <= 0 Or .Height < 0 Or .XPos < -50 Or .YPos < -50 Then
                Err.Raise CHQ_ERR_INVALID_COORD, "clsLayoutManager", .ObjectName
            End If
        End With
        Set m_Objects(m_ObjectCount) = o
        m_ObjectCount = m_ObjectCount + 1
        rs.MoveNext
    Loop
    rs.Close
    m_Loaded = True
    
    ' Push into cache
    Call StoreInCache
    LoadLayout = True
    Exit Function
Fail:
    LoadLayout = False
    m_Loaded = False
End Function

Private Sub StoreInCache()
    Dim i As Long
    Dim found As Long
    Dim entry As clsLayoutCacheEntry
    
    found = 0
    For i = 1 To m_Cache.Count
        Set entry = m_Cache(i)
        If entry.LayoutID = m_Current.LayoutID Then
            found = i
            Exit For
        End If
    Next i
    
    If found > 0 Then
        Set entry = m_Cache(found)
    Else
        Set entry = New clsLayoutCacheEntry
        m_Cache.Add entry
    End If
    
    entry.LayoutID = m_Current.LayoutID
    entry.BankID = m_Current.BankID
    entry.LayoutName = m_Current.LayoutName
    entry.ChequeWidth = m_Current.ChequeWidth
    entry.ChequeHeight = m_Current.ChequeHeight
    entry.TopMargin = m_Current.TopMargin
    entry.LeftMargin = m_Current.LeftMargin
    entry.PrinterDPI = m_Current.PrinterDPI
    entry.PaperOrientation = m_Current.PaperOrientation
    entry.PaperSizeName = m_Current.PaperSizeName
    entry.DateFormatCode = m_Current.DateFormatCode
    entry.AmountFormatCode = m_Current.AmountFormatCode
    entry.CurrencyPrefix = m_Current.CurrencyPrefix
    entry.ShowCurrencyPrefix = m_Current.ShowCurrencyPrefix
    entry.PayeeCaseMode = m_Current.PayeeCaseMode
    entry.PayeeMaxLength = m_Current.PayeeMaxLength
    entry.PayeeWrap = m_Current.PayeeWrap
    entry.PayeeAutoShrink = m_Current.PayeeAutoShrink
    entry.AutoCenter = m_Current.AutoCenter
    entry.Active = m_Current.Active
    Call entry.ClearObjects
    If m_ObjectCount > 0 Then
        For i = 0 To m_ObjectCount - 1
            Call entry.AddObject(m_Objects(i).CloneMe)
        Next i
    End If
    entry.Loaded = True
End Sub

Private Sub ApplyCacheEntry(ByVal entry As clsLayoutCacheEntry)
    Dim i As Long
    With m_Current
        .LayoutID = entry.LayoutID
        .BankID = entry.BankID
        .LayoutName = entry.LayoutName
        .ChequeWidth = entry.ChequeWidth
        .ChequeHeight = entry.ChequeHeight
        .TopMargin = entry.TopMargin
        .LeftMargin = entry.LeftMargin
        .PrinterDPI = entry.PrinterDPI
        .PaperOrientation = entry.PaperOrientation
        .PaperSizeName = entry.PaperSizeName
        .DateFormatCode = entry.DateFormatCode
        .AmountFormatCode = entry.AmountFormatCode
        .CurrencyPrefix = entry.CurrencyPrefix
        .ShowCurrencyPrefix = entry.ShowCurrencyPrefix
        .PayeeCaseMode = entry.PayeeCaseMode
        .PayeeMaxLength = entry.PayeeMaxLength
        .PayeeWrap = entry.PayeeWrap
        .PayeeAutoShrink = entry.PayeeAutoShrink
        .AutoCenter = entry.AutoCenter
        .Active = entry.Active
    End With
    m_ObjectCount = entry.ObjectCount
    If m_ObjectCount > 0 Then
        ReDim m_Objects(0 To m_ObjectCount - 1)
        For i = 0 To m_ObjectCount - 1
            Set m_Objects(i) = entry.LayoutObject(i).CloneMe
        Next i
    Else
        Erase m_Objects
    End If
    m_Loaded = True
End Sub

Public Function LoadDefaultLayoutForBank(ByVal lBankID As Long) As Long
    Dim rs As ADODB.Recordset
    Dim sSql As String
    Dim lID As Long
    sSql = "SELECT TOP 1 LayoutID FROM CHEQUE_LAYOUT_MASTER WHERE BankID=" & lBankID & _
           " AND Active=1 ORDER BY IsDefault DESC, LayoutID"
    Set rs = ChqOpenRs(sSql)
    If Not rs.EOF Then lID = NzLng(rs!LayoutID)
    rs.Close
    If lID > 0 Then
        If LoadLayout(lID) Then LoadDefaultLayoutForBank = lID
    End If
End Function

Public Sub LoadCalibration(ByVal sPrinterName As String, Optional ByVal lLayoutID As Long = 0)
    Dim rs As ADODB.Recordset
    Dim sSql As String
    OffsetLeft = 0: OffsetRight = 0: OffsetTop = 0: OffsetBottom = 0
    If lLayoutID = 0 Then lLayoutID = m_Current.LayoutID
    sSql = "SELECT TOP 1 OffsetLeft, OffsetRight, OffsetTop, OffsetBottom FROM CHEQUE_PRINTER_CALIBRATION " & _
           "WHERE CompanyID=" & CurrentChequeCompanyID() & " AND UserID='" & SqlSafe(CurrentChequeUserID()) & "'" & _
           " AND PrinterName='" & SqlSafe(sPrinterName) & "' AND (LayoutID=" & lLayoutID & " OR LayoutID IS NULL)" & _
           " ORDER BY CASE WHEN LayoutID=" & lLayoutID & " THEN 0 ELSE 1 END"
    On Error Resume Next
    Set rs = ChqOpenRs(sSql)
    If Not rs Is Nothing Then
        If Not rs.EOF Then
            OffsetLeft = NzDbl(rs!OffsetLeft)
            OffsetRight = NzDbl(rs!OffsetRight)
            OffsetTop = NzDbl(rs!OffsetTop)
            OffsetBottom = NzDbl(rs!OffsetBottom)
        End If
        rs.Close
    End If
End Sub

Public Sub SaveCalibration(ByVal sPrinterName As String, ByVal dblL As Double, ByVal dblR As Double, _
                           ByVal dblT As Double, ByVal dblB As Double, Optional ByVal lLayoutID As Long = 0)
    Dim sSql As String
    If lLayoutID = 0 Then lLayoutID = m_Current.LayoutID
    OffsetLeft = dblL: OffsetRight = dblR: OffsetTop = dblT: OffsetBottom = dblB
    sSql = "IF EXISTS (SELECT 1 FROM CHEQUE_PRINTER_CALIBRATION WHERE CompanyID=" & CurrentChequeCompanyID() & _
           " AND UserID='" & SqlSafe(CurrentChequeUserID()) & "' AND PrinterName='" & SqlSafe(sPrinterName) & _
           "' AND LayoutID=" & lLayoutID & ") " & _
           "UPDATE CHEQUE_PRINTER_CALIBRATION SET OffsetLeft=" & dblL & ", OffsetRight=" & dblR & _
           ", OffsetTop=" & dblT & ", OffsetBottom=" & dblB & ", ModifiedDate=GETDATE() " & _
           "WHERE CompanyID=" & CurrentChequeCompanyID() & " AND UserID='" & SqlSafe(CurrentChequeUserID()) & _
           "' AND PrinterName='" & SqlSafe(sPrinterName) & "' AND LayoutID=" & lLayoutID & " " & _
           "ELSE INSERT INTO CHEQUE_PRINTER_CALIBRATION (CompanyID,UserID,PrinterName,BankID,LayoutID,OffsetLeft,OffsetRight,OffsetTop,OffsetBottom) " & _
           "VALUES (" & CurrentChequeCompanyID() & ",'" & SqlSafe(CurrentChequeUserID()) & "','" & SqlSafe(sPrinterName) & "'," & _
           m_Current.BankID & "," & lLayoutID & "," & dblL & "," & dblR & "," & dblT & "," & dblB & ")"
    ChqExecute sSql
End Sub

Public Function SaveObject(ByVal o As clsLayoutObject) As Boolean
    Dim sSql As String
    On Error GoTo Fail
    If o.DetailID > 0 Then
        sSql = "UPDATE CHEQUE_LAYOUT_DETAIL SET ObjectName='" & SqlSafe(o.ObjectName) & "', ObjectCode='" & SqlSafe(o.ObjectCode) & "'" & _
               ", XPos=" & o.XPos & ", YPos=" & o.YPos & ", Width=" & o.Width & ", Height=" & o.Height & _
               ", FontName='" & SqlSafe(o.FontName) & "', FontSize=" & o.FontSize & _
               ", Bold=" & IIf(o.Bold, 1, 0) & ", Italic=" & IIf(o.Italic, 1, 0) & _
               ", Alignment=" & o.Alignment & ", Visible=" & IIf(o.Visible, 1, 0) & _
               ", Rotation=" & o.Rotation & ", PrintOrder=" & o.PrintOrder & _
               ", DefaultText='" & SqlSafe(o.DefaultText) & "', MinFontSize=" & o.MinFontSize & _
               ", ModifiedDate=GETDATE() WHERE DetailID=" & o.DetailID
    Else
        sSql = "INSERT INTO CHEQUE_LAYOUT_DETAIL (LayoutID,ObjectName,ObjectCode,XPos,YPos,Width,Height,FontName,FontSize,Bold,Italic,Alignment,Visible,Rotation,PrintOrder,DefaultText,MinFontSize) VALUES (" & _
               o.LayoutID & ",'" & SqlSafe(o.ObjectName) & "','" & SqlSafe(o.ObjectCode) & "'," & _
               o.XPos & "," & o.YPos & "," & o.Width & "," & o.Height & ",'" & SqlSafe(o.FontName) & "'," & _
               o.FontSize & "," & IIf(o.Bold, 1, 0) & "," & IIf(o.Italic, 1, 0) & "," & o.Alignment & "," & _
               IIf(o.Visible, 1, 0) & "," & o.Rotation & "," & o.PrintOrder & ",'" & SqlSafe(o.DefaultText) & "'," & o.MinFontSize & ")"
    End If
    ChqExecute sSql
    Call LoadLayout(o.LayoutID, True)
    SaveObject = True
    Exit Function
Fail:
    SaveObject = False
End Function

Public Function DeleteObject(ByVal lDetailID As Long, ByVal lLayoutID As Long) As Boolean
    On Error GoTo Fail
    ChqExecute "DELETE FROM CHEQUE_LAYOUT_DETAIL WHERE DetailID=" & lDetailID
    Call LoadLayout(lLayoutID, True)
    DeleteObject = True
    Exit Function
Fail:
    DeleteObject = False
End Function

Public Function EffectiveX(ByVal o As clsLayoutObject) As Double
    EffectiveX = m_Current.LeftMargin + o.XPos + OffsetLeft - OffsetRight
End Function

Public Function EffectiveY(ByVal o As clsLayoutObject) As Double
    EffectiveY = m_Current.TopMargin + o.YPos + OffsetTop - OffsetBottom
End Function
