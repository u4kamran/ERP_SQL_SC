Attribute VB_Name = "modChequeUtils"
'===============================================================================
' Shared utilities: formatting, case conversion, mm/twips, SQL helpers, UI msgs.
'===============================================================================
Option Explicit

Public Function MmToTwips(ByVal dblMm As Double) As Double
    MmToTwips = (dblMm / CHQ_MM_PER_INCH) * CHQ_TWIPS_PER_INCH
End Function

Public Function TwipsToMm(ByVal dblTwips As Double) As Double
    TwipsToMm = (dblTwips / CHQ_TWIPS_PER_INCH) * CHQ_MM_PER_INCH
End Function

Public Function MmToPixels(ByVal dblMm As Double, ByVal lDpi As Long) As Double
    If lDpi <= 0 Then lDpi = CHQ_DESIGNER_BASE_DPI
    MmToPixels = (dblMm / CHQ_MM_PER_INCH) * CDbl(lDpi)
End Function

Public Function PixelsToMm(ByVal dblPx As Double, ByVal lDpi As Long) As Double
    If lDpi <= 0 Then lDpi = CHQ_DESIGNER_BASE_DPI
    PixelsToMm = (dblPx / CDbl(lDpi)) * CHQ_MM_PER_INCH
End Function

Public Function SnapToGridMm(ByVal dblValue As Double, Optional ByVal dblGrid As Double = CHQ_GRID_SNAP_MM) As Double
    If dblGrid <= 0 Then
        SnapToGridMm = dblValue
    Else
        SnapToGridMm = Round(dblValue / dblGrid, 0) * dblGrid
    End If
End Function

Public Function SqlSafe(ByVal s As String) As String
    SqlSafe = Replace$(NzStr(s), "'", "''")
End Function

Public Function NzStr(ByVal v As Variant) As String
    If IsNull(v) Or IsEmpty(v) Then
        NzStr = vbNullString
    Else
        NzStr = CStr(v)
    End If
End Function

Public Function NzDbl(ByVal v As Variant, Optional ByVal dblDefault As Double = 0) As Double
    If IsNull(v) Or IsEmpty(v) Then
        NzDbl = dblDefault
    ElseIf Not IsNumeric(v) Then
        NzDbl = dblDefault
    Else
        NzDbl = CDbl(v)
    End If
End Function

Public Function NzLng(ByVal v As Variant, Optional ByVal lDefault As Long = 0) As Long
    If IsNull(v) Or IsEmpty(v) Then
        NzLng = lDefault
    ElseIf Not IsNumeric(v) Then
        NzLng = lDefault
    Else
        NzLng = CLng(v)
    End If
End Function

Public Function NzBool(ByVal v As Variant, Optional ByVal bDefault As Boolean = False) As Boolean
    If IsNull(v) Or IsEmpty(v) Then
        NzBool = bDefault
    Else
        NzBool = CBool(v)
    End If
End Function

Public Function ApplyPayeeCase(ByVal sText As String, ByVal eMode As eChqPayeeCase) As String
    Select Case eMode
        Case chqCaseUpper
            ApplyPayeeCase = UCase$(sText)
        Case chqCaseProper
            ApplyPayeeCase = StrConv(sText, vbProperCase)
        Case Else
            ApplyPayeeCase = sText
    End Select
End Function

Public Function FormatChequeDate(ByVal dt As Date, ByVal sFormatCode As String) As String
    Dim sCode As String
    sCode = UCase$(Trim$(sFormatCode))
    Select Case sCode
        Case "DD/MM/YYYY", "DD/MM/YY"
            FormatChequeDate = Format$(dt, "dd/mm/yyyy")
        Case "YYYY-MM-DD", "ISO"
            FormatChequeDate = Format$(dt, "yyyy-mm-dd")
        Case "SPACED", "DD      MM      YYYY"
            FormatChequeDate = Format$(dt, "dd") & "      " & Format$(dt, "mm") & "      " & Format$(dt, "yyyy")
        Case "DD-MMM-YYYY", "11-AUG-2026"
            FormatChequeDate = Format$(dt, "dd-mmm-yyyy")
        Case Else
            ' Allow raw VB Format patterns stored in DB
            On Error GoTo Fallback
            FormatChequeDate = Format$(dt, sFormatCode)
            Exit Function
Fallback:
            FormatChequeDate = Format$(dt, "dd-mmm-yyyy")
    End Select
End Function

Public Function FormatChequeAmount(ByVal dblAmt As Double, _
                                  ByVal sFormatCode As String, _
                                  ByVal sCurrency As String, _
                                  ByVal bShowPrefix As Boolean) As String
    Dim sFmt As String
    Dim sOut As String
    sFmt = Trim$(sFormatCode)
    If Len(sFmt) = 0 Then sFmt = "#,##0.00"
    On Error GoTo UseDefault
    sOut = Format$(dblAmt, sFmt)
    GoTo AddPrefix
UseDefault:
    sOut = Format$(dblAmt, "#,##0.00")
AddPrefix:
    If bShowPrefix And Len(Trim$(sCurrency)) > 0 Then
        FormatChequeAmount = Trim$(sCurrency) & " " & sOut
    Else
        FormatChequeAmount = sOut
    End If
End Function

Public Function TruncatePayee(ByVal sText As String, ByVal lMaxLen As Long) As String
    If lMaxLen <= 0 Then
        TruncatePayee = sText
    ElseIf Len(sText) <= lMaxLen Then
        TruncatePayee = sText
    Else
        TruncatePayee = Left$(sText, lMaxLen)
    End If
End Function

Public Sub ChqMsgInfo(ByVal sMsg As String)
    MsgBox sMsg, vbInformation + vbOKOnly, "Cheque Printing"
End Sub

Public Sub ChqMsgWarn(ByVal sMsg As String)
    MsgBox sMsg, vbExclamation + vbOKOnly, "Cheque Printing"
End Sub

Public Function ChqMsgAsk(ByVal sMsg As String) As VbMsgBoxResult
    ChqMsgAsk = MsgBox(sMsg, vbQuestion + vbYesNo, "Cheque Printing")
End Function

Public Sub ChqMsgError(ByVal sMsg As String)
    MsgBox sMsg, vbCritical + vbOKOnly, "Cheque Printing"
End Sub

Public Function FriendlyChequeError(ByVal lErr As Long, ByVal sDesc As String) As String
    Select Case lErr
        Case CHQ_ERR_LAYOUT_MISSING
            FriendlyChequeError = "Cheque layout is missing or inactive. Ask an administrator to configure a layout for this bank."
        Case CHQ_ERR_NO_PERMISSION
            FriendlyChequeError = "You do not have permission for this cheque operation."
        Case CHQ_ERR_ALREADY_PRINTED
            FriendlyChequeError = "This cheque has already been printed."
        Case CHQ_ERR_PRINTER
            FriendlyChequeError = "Printer problem: " & sDesc
        Case CHQ_ERR_INVALID_COORD
            FriendlyChequeError = "Invalid layout coordinates detected. Open the Layout Designer and correct the object positions."
        Case CHQ_ERR_DATABASE
            FriendlyChequeError = "Database error while processing cheque data." & vbCrLf & sDesc
        Case CHQ_ERR_NO_DATA
            FriendlyChequeError = "Voucher cheque data is incomplete (payee / amount / bank)."
        Case Else
            If InStr(1, LCase$(sDesc), "offline") > 0 Then
                FriendlyChequeError = "Printer Offline. Please check the printer power and network connection."
            ElseIf InStr(1, LCase$(sDesc), "paper") > 0 Then
                FriendlyChequeError = "Paper problem (jam / no paper). Clear the printer and retry."
            Else
                FriendlyChequeError = "Cheque printing error: " & sDesc
            End If
    End Select
End Function

'--- ADO open helper using global Con (ERP convention)
Public Function ChqOpenRs(ByVal sSql As String, Optional ByVal lCursor As Long = adOpenStatic, Optional ByVal lLock As Long = adLockReadOnly) As ADODB.Recordset
    Dim rs As ADODB.Recordset
    Set rs = New ADODB.Recordset
    rs.CursorLocation = adUseClient
    rs.Open sSql, Con, lCursor, lLock
    Set ChqOpenRs = rs
End Function

Public Sub ChqExecute(ByVal sSql As String)
    Dim cmd As ADODB.Command
    Set cmd = New ADODB.Command
    With cmd
        .ActiveConnection = Con
        .CommandType = adCmdText
        .CommandText = sSql
        .Execute
    End With
End Sub

Public Function CurrentChequeUserID() As String
    ' Prefer ERP globals when present
    On Error Resume Next
    If Len(cLoginName) > 0 Then
        CurrentChequeUserID = cLoginName
    ElseIf Len(cUserName) > 0 Then
        CurrentChequeUserID = cUserName
    Else
        CurrentChequeUserID = Environ$("USERNAME")
    End If
End Function

Public Function CurrentChequeCompanyID() As Long
    On Error Resume Next
    ' Prefer ERP GVar.CompanyID when present; fall back to cCompanyID / 1
    If GVar.CompanyID > 0 Then
        CurrentChequeCompanyID = CLng(GVar.CompanyID)
        Exit Function
    End If
    If IsNumeric(cCompanyID) Then
        CurrentChequeCompanyID = CLng(cCompanyID)
    End If
    If Err.Number <> 0 Or CurrentChequeCompanyID <= 0 Then CurrentChequeCompanyID = 1
End Function
