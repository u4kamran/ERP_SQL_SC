VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
  Persistable = 0  'NotPersistable
  DataBindingBehavior = 0  'vbNone
  DataSourceBehavior = 0   'vbNone
  MTSTransactionMode = 0   'NotAnMTSObject
END
Attribute VB_Name = "clsPrinterManager"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
'===============================================================================
' Printer selection: Windows default, bank default, last used, or explicit pick.
' Remembers user preference in CHEQUE_USER_PREFERENCE.
'===============================================================================
Option Explicit

Private m_Printers() As String
Private m_Count As Long

Public Property Get PrinterCount() As Long
    PrinterCount = m_Count
End Property

Public Property Get PrinterName(ByVal Index As Long) As String
    If Index >= 0 And Index < m_Count Then PrinterName = m_Printers(Index)
End Property

Public Sub RefreshPrinterList()
    Dim i As Long
    Dim n As Long
    On Error GoTo Fail
    n = Printers.Count
    If n <= 0 Then
        m_Count = 0
        Erase m_Printers
        Exit Sub
    End If
    ReDim m_Printers(0 To n - 1)
    m_Count = n
    For i = 0 To n - 1
        m_Printers(i) = Printers(i).DeviceName
    Next i
    Exit Sub
Fail:
    m_Count = 0
End Sub

Public Function ResolvePrinter(ByVal eMode As eChqPrinterMode, _
                               Optional ByVal sBankPrinter As String = "", _
                               Optional ByVal sExplicit As String = "") As String
    Dim sLast As String
    Dim sWin As String
    
    Select Case eMode
        Case chqPrinterSelect
            ResolvePrinter = sExplicit
        Case chqPrinterBankDefault
            If Len(Trim$(sBankPrinter)) > 0 Then
                ResolvePrinter = sBankPrinter
            Else
                ResolvePrinter = WindowsDefaultPrinterName()
            End If
        Case chqPrinterLastUsed
            sLast = GetPreference(CHQ_PREF_LAST_PRINTER)
            If Len(sLast) > 0 Then
                ResolvePrinter = sLast
            Else
                ResolvePrinter = WindowsDefaultPrinterName()
            End If
        Case Else
            sWin = WindowsDefaultPrinterName()
            ResolvePrinter = sWin
    End Select
    
    If Len(Trim$(ResolvePrinter)) = 0 Then
        Me.RefreshPrinterList
        If m_Count > 0 Then ResolvePrinter = m_Printers(0)
    End If
End Function

Public Function SetActivePrinter(ByVal sPrinterName As String) As Boolean
    Dim i As Long
    On Error GoTo Fail
    If Len(Trim$(sPrinterName)) = 0 Then
        SetActivePrinter = False
        Exit Function
    End If
    For i = 0 To Printers.Count - 1
        If StrComp(Printers(i).DeviceName, sPrinterName, vbTextCompare) = 0 Then
            Set Printer = Printers(i)
            SetActivePrinter = True
            Call SavePreference(CHQ_PREF_LAST_PRINTER, sPrinterName)
            Exit Function
        End If
    Next i
    SetActivePrinter = False
    Exit Function
Fail:
    SetActivePrinter = False
End Function

Public Function ValidatePrinterReady(ByVal sPrinterName As String, ByRef sMessage As String) As Boolean
    ' Best-effort: VB6 Printer object cannot always read spooler status.
    ' We verify the device exists; offline/jam messages come from print failures.
    Dim i As Long
    On Error GoTo Fail
    For i = 0 To Printers.Count - 1
        If StrComp(Printers(i).DeviceName, sPrinterName, vbTextCompare) = 0 Then
            ValidatePrinterReady = True
            sMessage = "Ready"
            Exit Function
        End If
    Next i
    ValidatePrinterReady = False
    sMessage = "Wrong Printer / Printer not found: " & sPrinterName
    Exit Function
Fail:
    ValidatePrinterReady = False
    sMessage = Err.Description
End Function

Public Sub ApplyPaperSettings(ByVal sPaperSizeName As String, ByVal eOrient As eChqOrientation, _
                              ByVal dblWidthMm As Double, ByVal dblHeightMm As Double)
    On Error Resume Next
    Select Case UCase$(Trim$(sPaperSizeName))
        Case "A4"
            Printer.PaperSize = vbPRPSA4
        Case "LETTER"
            Printer.PaperSize = vbPRPSLetter
        Case "LEGAL"
            Printer.PaperSize = vbPRPSLegal
        Case Else
            ' Custom — set dimensions in twips where driver allows
            Printer.PaperSize = vbPRPSUser
            Printer.Width = CInt(MmToTwips(dblWidthMm))
            Printer.Height = CInt(MmToTwips(dblHeightMm))
    End Select
    If eOrient = chqLandscape Then
        Printer.Orientation = vbPRORLandscape
    Else
        Printer.Orientation = vbPRORPortrait
    End If
End Sub

Public Function GetPreference(ByVal sKey As String) As String
    Dim rs As ADODB.Recordset
    Dim sSql As String
    On Error GoTo Fail
    sSql = "SELECT PrefValue FROM CHEQUE_USER_PREFERENCE WHERE CompanyID=" & CurrentChequeCompanyID() & _
           " AND UserID='" & SqlSafe(CurrentChequeUserID()) & "' AND PrefKey='" & SqlSafe(sKey) & "'"
    Set rs = ChqOpenRs(sSql)
    If Not rs.EOF Then GetPreference = NzStr(rs!PrefValue)
    rs.Close
    Exit Function
Fail:
    GetPreference = vbNullString
End Function

Public Sub SavePreference(ByVal sKey As String, ByVal sValue As String)
    Dim sSql As String
    On Error Resume Next
    sSql = "IF EXISTS (SELECT 1 FROM CHEQUE_USER_PREFERENCE WHERE CompanyID=" & CurrentChequeCompanyID() & _
           " AND UserID='" & SqlSafe(CurrentChequeUserID()) & "' AND PrefKey='" & SqlSafe(sKey) & "') " & _
           "UPDATE CHEQUE_USER_PREFERENCE SET PrefValue='" & SqlSafe(sValue) & "', ModifiedDate=GETDATE() " & _
           "WHERE CompanyID=" & CurrentChequeCompanyID() & " AND UserID='" & SqlSafe(CurrentChequeUserID()) & _
           "' AND PrefKey='" & SqlSafe(sKey) & "' " & _
           "ELSE INSERT INTO CHEQUE_USER_PREFERENCE (CompanyID, UserID, PrefKey, PrefValue) VALUES (" & _
           CurrentChequeCompanyID() & ",'" & SqlSafe(CurrentChequeUserID()) & "','" & SqlSafe(sKey) & "','" & SqlSafe(sValue) & "')"
    ChqExecute sSql
End Sub

Public Sub FillCombo(ByVal cbo As Object)
    Dim i As Long
    On Error Resume Next
    Me.RefreshPrinterList
    cbo.Clear
    For i = 0 To m_Count - 1
        cbo.AddItem m_Printers(i)
    Next i
End Sub
