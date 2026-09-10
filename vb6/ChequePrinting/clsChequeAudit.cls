VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
  Persistable = 0  'NotPersistable
  DataBindingBehavior = 0  'vbNone
  DataSourceBehavior = 0   'vbNone
  MTSTransactionMode = 0   'NotAnMTSObject
END
Attribute VB_Name = "clsChequeAudit"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
'===============================================================================
' Permissions, print register, audit trail, status updates (transactional).
'===============================================================================
Option Explicit

Public Function HasPermission(ByVal sPermCode As String, Optional ByVal sUserID As String = "") As Boolean
    Dim rs As ADODB.Recordset
    Dim sSql As String
    On Error GoTo Fail
    If Len(sUserID) = 0 Then sUserID = CurrentChequeUserID()
    
    ' Super-user shortcut used by many VB6 ERPs
    On Error Resume Next
    If UCase$(sUserID) = "ADMIN" Or UCase$(sUserID) = "SA" Or UCase$(cLoginName) = "SA" Then
        HasPermission = True
        Exit Function
    End If
    On Error GoTo Fail
    
    sSql = "SELECT Allowed FROM CHEQUE_PERMISSION WHERE UserID='" & SqlSafe(sUserID) & "'" & _
           " AND PermissionCode='" & SqlSafe(sPermCode) & "'"
    Set rs = ChqOpenRs(sSql)
    If Not rs.EOF Then
        HasPermission = NzBool(rs!Allowed)
    Else
        HasPermission = False
    End If
    rs.Close
    Exit Function
Fail:
    HasPermission = False
End Function

Public Function EnsurePermission(ByVal sPermCode As String) As Boolean
    If HasPermission(sPermCode) Then
        EnsurePermission = True
    Else
        Err.Raise CHQ_ERR_NO_PERMISSION, "clsChequeAudit", sPermCode
    End If
End Function

Public Function UpsertRegister(ByVal d As clsChequeData, ByVal lLayoutID As Long, _
                               ByVal bIsReprint As Boolean, ByVal sPrinter As String) As Long
    Dim sSql As String
    Dim rs As ADODB.Recordset
    Dim sStatus As String
    Dim lReg As Long
    
    On Error GoTo Fail
    d.EnsureAmountInWords
    sStatus = IIf(bIsReprint, CHQ_STATUS_REPRINTED, CHQ_STATUS_PRINTED)
    lReg = d.RegisterID
    
    Con.BeginTrans
    
    If lReg > 0 Then
        sSql = "UPDATE CHEQUE_PRINT_REGISTER SET PayeeName='" & SqlSafe(d.PayeeName) & "'" & _
               ", Amount=" & d.Amount & ", CurrencyCode='" & SqlSafe(d.CurrencyCode) & "'" & _
               ", AmountInWords='" & SqlSafe(d.AmountInWords) & "', Narration='" & SqlSafe(d.Narration) & "'" & _
               ", BankID=" & d.BankID & ", BankAccount='" & SqlSafe(d.BankAccount) & "'" & _
               ", ChequeNo='" & SqlSafe(d.ChequeNo) & "', ChequeDate='" & Format$(d.ChequeDate, "yyyy-mm-dd") & "'" & _
               ", LayoutID=" & lLayoutID & ", StatusCode='" & sStatus & "'" & _
               ", PrintCount=PrintCount+1" & _
               ", LastPrintedBy='" & SqlSafe(CurrentChequeUserID()) & "'" & _
               ", LastPrintedDate=GETDATE()" & _
               ", LastPrinterName='" & SqlSafe(sPrinter) & "'" & _
               ", LastComputerName='" & SqlSafe(ChequeComputerName()) & "'" & _
               ", ModifiedBy='" & SqlSafe(CurrentChequeUserID()) & "', ModifiedDate=GETDATE()" & _
               " WHERE RegisterID=" & lReg
        ChqExecute sSql
    Else
        sSql = "INSERT INTO CHEQUE_PRINT_REGISTER (" & _
               "CompanyID,BranchID,VoucherNo,VoucherDate,VoucherSerial,DocTypeID,Fiscal,PartyID,PayeeName," & _
               "Amount,CurrencyCode,AmountInWords,Narration,BankID,BankAccount,ChequeNo,ChequeDate,LayoutID," & _
               "StatusCode,PrintCount,LastPrintedBy,LastPrintedDate,LastPrinterName,LastComputerName,CreatedBy)" & _
               " VALUES (" & _
               d.CompanyID & "," & d.BranchID & ",'" & SqlSafe(d.VoucherNo) & "','" & Format$(d.VoucherDate, "yyyy-mm-dd") & "'," & _
               d.VoucherSerial & "," & d.DocTypeID & "," & d.Fiscal & "," & d.PartyID & ",'" & SqlSafe(d.PayeeName) & "'," & _
               d.Amount & ",'" & SqlSafe(d.CurrencyCode) & "','" & SqlSafe(d.AmountInWords) & "','" & SqlSafe(d.Narration) & "'," & _
               d.BankID & ",'" & SqlSafe(d.BankAccount) & "','" & SqlSafe(d.ChequeNo) & "','" & Format$(d.ChequeDate, "yyyy-mm-dd") & "'," & _
               lLayoutID & ",'" & sStatus & "',1,'" & SqlSafe(CurrentChequeUserID()) & "',GETDATE(),'" & _
               SqlSafe(sPrinter) & "','" & SqlSafe(ChequeComputerName()) & "','" & SqlSafe(CurrentChequeUserID()) & "')"
        ChqExecute sSql
        Set rs = ChqOpenRs("SELECT MAX(RegisterID) AS RID FROM CHEQUE_PRINT_REGISTER WHERE CompanyID=" & d.CompanyID & _
                           " AND ChequeNo='" & SqlSafe(d.ChequeNo) & "' AND BankID=" & d.BankID)
        If Not rs.EOF Then lReg = NzLng(rs!RID)
        rs.Close
        d.RegisterID = lReg
    End If
    
    Call WriteAudit(lReg, IIf(bIsReprint, CHQ_ACT_REPRINT, CHQ_ACT_PRINT), d, lLayoutID, sPrinter, bIsReprint, 1, "")
    
    ' Queue Positive Pay (future)
    On Error Resume Next
    ChqExecute "INSERT INTO CHEQUE_POSITIVE_PAY_QUEUE (RegisterID, BankID) VALUES (" & lReg & "," & d.BankID & ")"
    On Error GoTo Fail
    
    Con.CommitTrans
    UpsertRegister = lReg
    Exit Function
Fail:
    On Error Resume Next
    Con.RollbackTrans
    Err.Raise CHQ_ERR_DATABASE, "clsChequeAudit.UpsertRegister", Err.Description
End Function

Public Sub WriteAudit(ByVal lRegisterID As Long, ByVal sAction As String, ByVal d As clsChequeData, _
                      ByVal lLayoutID As Long, ByVal sPrinter As String, ByVal bReprint As Boolean, _
                      ByVal lCopies As Long, ByVal sRemarks As String)
    Dim sSql As String
    sSql = "INSERT INTO CHEQUE_PRINT_AUDIT (RegisterID,ActionCode,VoucherNo,ChequeNo,LayoutID,PrintedBy,PrintedDate,PrintedTime,PrinterName,ComputerName,Copies,Remarks,IsReprint) VALUES (" & _
           IIf(lRegisterID > 0, CStr(lRegisterID), "NULL") & ",'" & SqlSafe(sAction) & "','" & SqlSafe(d.VoucherNo) & "','" & _
           SqlSafe(d.ChequeNo) & "'," & lLayoutID & ",'" & SqlSafe(CurrentChequeUserID()) & "',GETDATE(),'" & _
           Format$(Now, "hh:nn:ss") & "','" & SqlSafe(sPrinter) & "','" & SqlSafe(ChequeComputerName()) & "'," & _
           lCopies & ",'" & SqlSafe(sRemarks) & "'," & IIf(bReprint, 1, 0) & ")"
    ChqExecute sSql
End Sub

Public Sub UpdateStatus(ByVal lRegisterID As Long, ByVal sStatus As String, ByVal sRemarks As String)
    Dim d As New clsChequeData
    Dim sSql As String
    Call EnsurePermission(CHQ_PERM_CANCEL)
    Con.BeginTrans
    sSql = "UPDATE CHEQUE_PRINT_REGISTER SET StatusCode='" & SqlSafe(sStatus) & "'" & _
           ", ModifiedBy='" & SqlSafe(CurrentChequeUserID()) & "', ModifiedDate=GETDATE() WHERE RegisterID=" & lRegisterID
    ChqExecute sSql
    d.RegisterID = lRegisterID
    Call WriteAudit(lRegisterID, IIf(sStatus = CHQ_STATUS_VOIDED, CHQ_ACT_VOID, CHQ_ACT_CANCEL), d, 0, "", False, 0, sRemarks)
    Con.CommitTrans
End Sub
