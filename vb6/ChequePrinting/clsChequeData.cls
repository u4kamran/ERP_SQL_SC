VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
  Persistable = 0  'NotPersistable
  DataBindingBehavior = 0  'vbNone
  DataSourceBehavior = 0   'vbNone
  MTSTransactionMode = 0   'NotAnMTSObject
END
Attribute VB_Name = "clsChequeData"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
'===============================================================================
' Cheque print DTO — loaded from current voucher (no re-entry).
'===============================================================================
Option Explicit

Public CompanyID As Long
Public BranchID As Long
Public CompanyName As String
Public BranchName As String
Public UserID As String
Public UserName As String

Public VoucherNo As String
Public VoucherDate As Date
Public VoucherSerial As Long
Public DocTypeID As Long
Public Fiscal As Integer

Public PartyID As Long
Public PayeeName As String          ' AC_TITLE
Public Amount As Double
Public CurrencyCode As String
Public AmountInWords As String
Public Narration As String

Public BankID As Long
Public BankName As String
Public BankAccount As String
Public BankAccountID As Long
Public ChequeNo As String
Public ChequeDate As Date
Public LayoutID As Long
Public ChequeBookID As Long

Public RegisterID As Long
Public StatusCode As String
Public PrintCount As Long

Public Function IsValid(ByRef sMsg As String) As Boolean
    If Len(Trim$(PayeeName)) = 0 Then
        sMsg = "Payee name (AC_TITLE) is missing on the voucher."
        IsValid = False
        Exit Function
    End If
    If Amount <= 0 Then
        sMsg = "Cheque amount must be greater than zero."
        IsValid = False
        Exit Function
    End If
    If Len(Trim$(ChequeNo)) = 0 Then
        sMsg = "Cheque number is required."
        IsValid = False
        Exit Function
    End If
    If BankID <= 0 And Len(Trim$(BankAccount)) = 0 Then
        sMsg = "Bank account is not identified on this voucher."
        IsValid = False
        Exit Function
    End If
    IsValid = True
End Function

Public Sub EnsureAmountInWords()
    Dim oWords As clsAmountToWords
    If Len(Trim$(AmountInWords)) = 0 Then
        Set oWords = New clsAmountToWords
        AmountInWords = oWords.ToWords(Amount, CurrencyCode, True)
    End If
End Sub

'-------------------------------------------------------------------------------
' Load from voucher tables (ERP: gl0002 header + party title).
' Adjust column names if your voucher schema differs — keep this as the single
' mapping point.
'-------------------------------------------------------------------------------
Public Function LoadFromVoucher(ByVal sVoucherNo As String, _
                                Optional ByVal lSerial As Long = 0, _
                                Optional ByVal lDocType As Long = 0, _
                                Optional ByVal nFiscal As Integer = 0) As Boolean
    Dim rs As ADODB.Recordset
    Dim sSql As String
    Dim oWords As clsAmountToWords
    On Error GoTo Fail
    
    CompanyID = CurrentChequeCompanyID()
    UserID = CurrentChequeUserID()
    On Error Resume Next
    UserName = cUserName
    CompanyName = cName
    On Error GoTo Fail
    
    ' Header — prefer serial when provided
    If lSerial > 0 Then
        sSql = "SELECT TOP 1 * FROM gl0002 WHERE SERIAL_NO=" & lSerial
        If lDocType > 0 Then sSql = sSql & " AND DOC_TYPE_ID=" & lDocType
        If nFiscal >= 0 Then sSql = sSql & " AND FISCAL=" & nFiscal
    Else
        sSql = "SELECT TOP 1 * FROM gl0002 WHERE VOUCHER_NO='" & SqlSafe(sVoucherNo) & "' OR CONVERT(VARCHAR(40), VOUCHER_ID)='" & SqlSafe(sVoucherNo) & "'"
    End If
    
    Set rs = ChqOpenRs(sSql)
    If rs.EOF Then
        rs.Close
        ' Fallback: try Fin payment voucher style if present
        sSql = "SELECT TOP 1 * FROM Fin_Pay_M WHERE CONVERT(VARCHAR(40), PROD_ID)='" & SqlSafe(sVoucherNo) & "'"
        On Error Resume Next
        Set rs = ChqOpenRs(sSql)
        On Error GoTo Fail
        If rs Is Nothing Or rs.EOF Then
            Err.Raise CHQ_ERR_NO_DATA, "clsChequeData", "Voucher not found"
        End If
        Call MapFinPay(rs)
        rs.Close
        LoadFromVoucher = True
        Exit Function
    End If
    
    Call MapGl0002(rs)
    rs.Close
    
    ' Resolve AC_TITLE from chart / party
    If Len(Trim$(PayeeName)) = 0 And PartyID > 0 Then
        sSql = "SELECT TOP 1 AC_TITLE FROM gl0001 WHERE AC_ID=" & PartyID
        Set rs = ChqOpenRs(sSql)
        If Not rs.EOF Then PayeeName = NzStr(rs!AC_TITLE)
        rs.Close
    End If
    
    If Len(Trim$(CurrencyCode)) = 0 Then CurrencyCode = "PKR"
    Set oWords = New clsAmountToWords
    AmountInWords = oWords.ToWords(Amount, CurrencyCode, True)
    
    Call TryResolveBank
    Call TryLoadRegister
    
    LoadFromVoucher = True
    Exit Function
Fail:
    LoadFromVoucher = False
End Function

Private Sub MapGl0002(ByVal rs As ADODB.Recordset)
    On Error Resume Next
    VoucherNo = NzStr(rs!VOUCHER_NO)
    If Len(VoucherNo) = 0 Then VoucherNo = NzStr(rs!VOUCHER_ID)
    VoucherDate = CDate(rs!VOUCHER_DATE)
    If Err.Number <> 0 Then
        Err.Clear
        VoucherDate = CDate(rs!DOC_DATE)
    End If
    VoucherSerial = NzLng(rs!SERIAL_NO)
    DocTypeID = NzLng(rs!DOC_TYPE_ID)
    Fiscal = NzLng(rs!FISCAL)
    PartyID = NzLng(rs!AC_ID)
    If PartyID = 0 Then PartyID = NzLng(rs!PARTY_ID)
    PayeeName = NzStr(rs!AC_TITLE)
    Amount = NzDbl(rs!AMOUNT)
    If Amount = 0 Then Amount = NzDbl(rs!TOTAL_AMT)
    Narration = NzStr(rs!NARRATION)
    If Len(Narration) = 0 Then Narration = NzStr(rs!REMARKS)
    ChequeNo = NzStr(rs!CHEQUE_NO)
    If Len(ChequeNo) = 0 Then ChequeNo = NzStr(rs!CHQ_NO)
    If Not IsNull(rs!CHEQUE_DATE) Then ChequeDate = CDate(rs!CHEQUE_DATE)
    If ChequeDate = 0 Then ChequeDate = VoucherDate
    BankAccount = NzStr(rs!BANK_ACCOUNT)
    BankAccountID = NzLng(rs!BANK_AC_ID)
    CurrencyCode = NzStr(rs!CURRENCY_CODE)
    BranchID = NzLng(rs!BRANCH_ID)
End Sub

Private Sub MapFinPay(ByVal rs As ADODB.Recordset)
    On Error Resume Next
    VoucherNo = NzStr(rs!PROD_ID)
    VoucherDate = CDate(rs!DOC_DATE)
    VoucherSerial = NzLng(rs!SERIAL_NO)
    PartyID = NzLng(rs!SUPPLIER_ID)
    If PartyID = 0 Then PartyID = NzLng(rs!AC_ID)
    PayeeName = NzStr(rs!vendor_title)
    Amount = NzDbl(rs!TOTAL_AMT)
    If Amount = 0 Then Amount = NzDbl(rs!AMOUNT)
    Narration = NzStr(rs!REMARKS)
    ChequeNo = NzStr(rs!CHEQUE_NO)
    ChequeDate = VoucherDate
    CurrencyCode = "PKR"
End Sub

Private Sub TryResolveBank()
    Dim rs As ADODB.Recordset
    Dim sSql As String
    On Error Resume Next
    If BankID > 0 Then Exit Sub
    If BankAccountID > 0 Then
        sSql = "SELECT TOP 1 BankID, BankName FROM BANK_MASTER WHERE BankID IN (" & _
               "SELECT BankID FROM CHEQUE_BOOK WHERE BankAccountID=" & BankAccountID & ")"
        Set rs = ChqOpenRs(sSql)
        If Not rs.EOF Then
            BankID = NzLng(rs!BankID)
            BankName = NzStr(rs!BankName)
        End If
        If Not rs Is Nothing Then If rs.State = adStateOpen Then rs.Close
    End If
    If BankID = 0 Then
        sSql = "SELECT TOP 1 BankID, BankName, DefaultPrinter FROM BANK_MASTER WHERE Active=1 ORDER BY BankID"
        Set rs = ChqOpenRs(sSql)
        If Not rs.EOF Then
            BankID = NzLng(rs!BankID)
            BankName = NzStr(rs!BankName)
        End If
        If Not rs Is Nothing Then If rs.State = adStateOpen Then rs.Close
    End If
End Sub

Private Sub TryLoadRegister()
    Dim rs As ADODB.Recordset
    Dim sSql As String
    On Error Resume Next
    sSql = "SELECT TOP 1 * FROM CHEQUE_PRINT_REGISTER WHERE CompanyID=" & CompanyID & _
           " AND VoucherNo='" & SqlSafe(VoucherNo) & "'"
    If Len(ChequeNo) > 0 Then
        sSql = "SELECT TOP 1 * FROM CHEQUE_PRINT_REGISTER WHERE CompanyID=" & CompanyID & _
               " AND ((BankID=" & BankID & " AND ChequeNo='" & SqlSafe(ChequeNo) & "') OR VoucherNo='" & SqlSafe(VoucherNo) & "')"
    End If
    Set rs = ChqOpenRs(sSql)
    If Not rs.EOF Then
        RegisterID = NzLng(rs!RegisterID)
        StatusCode = NzStr(rs!StatusCode)
        PrintCount = NzLng(rs!PrintCount)
        LayoutID = NzLng(rs!LayoutID)
        If Len(ChequeNo) = 0 Then ChequeNo = NzStr(rs!ChequeNo)
    Else
        StatusCode = CHQ_STATUS_DRAFT
        PrintCount = 0
    End If
    If Not rs Is Nothing Then If rs.State = adStateOpen Then rs.Close
End Sub

Public Function AlreadyPrinted() As Boolean
    AlreadyPrinted = (PrintCount > 0) Or (StatusCode = CHQ_STATUS_PRINTED) Or (StatusCode = CHQ_STATUS_REPRINTED)
End Function
