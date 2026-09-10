VERSION 5.00
Object = "{5E9E78A0-531B-11CF-91F6-C2863C385E30}#1.0#0"; "MSFLXGRD.OCX"
Object = "{86CF1D34-0C5F-11D2-A9FC-0000F8754DA1}#2.0#0"; "MSCOMCT2.OCX"
Begin VB.Form frmChequeSearch 
   Caption         =   "Cheque Register Search"
   ClientHeight    =   7800
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   12800
   LinkTopic       =   "Form1"
   ScaleHeight     =   7800
   ScaleWidth      =   12800
   StartUpPosition =   2  'CenterScreen
   Begin VB.TextBox txtVoucher 
      Height          =   315
      Left            =   1200
      TabIndex        =   14
      Top             =   120
      Width           =   1455
   End
   Begin VB.TextBox txtCheque 
      Height          =   315
      Left            =   3840
      TabIndex        =   13
      Top             =   120
      Width           =   1455
   End
   Begin VB.TextBox txtParty 
      Height          =   315
      Left            =   6360
      TabIndex        =   12
      Top             =   120
      Width           =   2055
   End
   Begin VB.TextBox txtAmount 
      Height          =   315
      Left            =   9600
      TabIndex        =   11
      Top             =   120
      Width           =   1215
   End
   Begin VB.ComboBox cboBank 
      Height          =   315
      Left            =   1200
      Style           =   2  'Dropdown List
      TabIndex        =   10
      Top             =   600
      Width           =   2055
   End
   Begin VB.ComboBox cboStatus 
      Height          =   315
      Left            =   4200
      Style           =   2  'Dropdown List
      TabIndex        =   9
      Top             =   600
      Width           =   1455
   End
   Begin VB.TextBox txtPrintedBy 
      Height          =   315
      Left            =   6960
      TabIndex        =   8
      Top             =   600
      Width           =   1575
   End
   Begin MSComCtl2.DTPicker dtFrom 
      Height          =   315
      Left            =   1200
      TabIndex        =   7
      Top             =   1080
      Width           =   1455
      _ExtentX        =   2566
      _ExtentY        =   556
      _Version        =   393216
      Format          =   123207681
      CurrentDate     =   44927
   End
   Begin MSComCtl2.DTPicker dtTo 
      Height          =   315
      Left            =   3480
      TabIndex        =   6
      Top             =   1080
      Width           =   1455
      _ExtentX        =   2566
      _ExtentY        =   556
      _Version        =   393216
      Format          =   123207681
      CurrentDate     =   44927
   End
   Begin VB.CommandButton cmdSearch 
      Caption         =   "&Search"
      Height          =   375
      Left            =   5280
      TabIndex        =   5
      Top             =   1080
      Width           =   1215
   End
   Begin VB.CommandButton cmdPreview 
      Caption         =   "Pre&view"
      Height          =   375
      Left            =   6600
      TabIndex        =   4
      Top             =   1080
      Width           =   1215
   End
   Begin VB.CommandButton cmdExport 
      Caption         =   "&Export CSV"
      Height          =   375
      Left            =   7920
      TabIndex        =   3
      Top             =   1080
      Width           =   1215
   End
   Begin VB.CommandButton cmdClose 
      Cancel          =   -1  'True
      Caption         =   "&Close"
      Height          =   375
      Left            =   11400
      TabIndex        =   2
      Top             =   7200
      Width           =   1215
   End
   Begin MSFlexGridLib.MSFlexGrid grd 
      Height          =   5415
      Left            =   120
      TabIndex        =   1
      Top             =   1560
      Width           =   12495
      _ExtentX        =   22040
      _ExtentY        =   9551
      _Version        =   393216
      Cols            =   11
      FixedCols       =   0
      AllowUserResizing=   1
   End
   Begin VB.Label lbl1 
      Caption         =   "Voucher"
      Height          =   255
      Left            =   120
      TabIndex        =   0
      Top             =   150
      Width           =   975
   End
   Begin VB.Label lbl2 
      Caption         =   "Cheque#"
      Height          =   255
      Left            =   2880
      TabIndex        =   15
      Top             =   150
      Width           =   855
   End
   Begin VB.Label lbl3 
      Caption         =   "Party"
      Height          =   255
      Left            =   5520
      TabIndex        =   16
      Top             =   150
      Width           =   735
   End
   Begin VB.Label lbl4 
      Caption         =   "Amount"
      Height          =   255
      Left            =   8760
      TabIndex        =   17
      Top             =   150
      Width           =   735
   End
   Begin VB.Label lbl5 
      Caption         =   "Bank"
      Height          =   255
      Left            =   120
      TabIndex        =   18
      Top             =   630
      Width           =   735
   End
   Begin VB.Label lbl6 
      Caption         =   "Status"
      Height          =   255
      Left            =   3480
      TabIndex        =   19
      Top             =   630
      Width           =   735
   End
   Begin VB.Label lbl7 
      Caption         =   "Printed By"
      Height          =   255
      Left            =   5880
      TabIndex        =   20
      Top             =   630
      Width           =   975
   End
   Begin VB.Label lbl8 
      Caption         =   "From"
      Height          =   255
      Left            =   120
      TabIndex        =   21
      Top             =   1110
      Width           =   735
   End
   Begin VB.Label lbl9 
      Caption         =   "To"
      Height          =   255
      Left            =   2880
      TabIndex        =   22
      Top             =   1110
      Width           =   495
   End
End
Attribute VB_Name = "frmChequeSearch"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Sub Form_Load()
    Dim audit As New clsChequeAudit
    Dim rs As ADODB.Recordset
    If Not audit.HasPermission(CHQ_PERM_HISTORY) Then
        ChqMsgError "No permission."
        Unload Me
        Exit Sub
    End If
    dtFrom.Value = DateAdd("m", -1, Date)
    dtTo.Value = Date
    cboStatus.Clear
    cboStatus.AddItem "(All)"
    cboStatus.AddItem CHQ_STATUS_DRAFT
    cboStatus.AddItem CHQ_STATUS_PRINTED
    cboStatus.AddItem CHQ_STATUS_REPRINTED
    cboStatus.AddItem CHQ_STATUS_CANCELLED
    cboStatus.AddItem CHQ_STATUS_VOIDED
    cboStatus.AddItem CHQ_STATUS_CLEARED
    cboStatus.AddItem CHQ_STATUS_BOUNCED
    cboStatus.ListIndex = 0
    
    cboBank.Clear
    cboBank.AddItem "(All)"
    cboBank.ItemData(cboBank.NewIndex) = 0
    Set rs = ChqOpenRs("SELECT BankID, BankName FROM BANK_MASTER WHERE Active=1 ORDER BY BankName")
    Do While Not rs.EOF
        cboBank.AddItem NzStr(rs!BankName)
        cboBank.ItemData(cboBank.NewIndex) = NzLng(rs!BankID)
        rs.MoveNext
    Loop
    rs.Close
    cboBank.ListIndex = 0
    
    With grd
        .Rows = 1: .Cols = 11
        .TextMatrix(0, 0) = "RegisterID"
        .TextMatrix(0, 1) = "Voucher"
        .TextMatrix(0, 2) = "Cheque#"
        .TextMatrix(0, 3) = "Payee"
        .TextMatrix(0, 4) = "Amount"
        .TextMatrix(0, 5) = "Date"
        .TextMatrix(0, 6) = "Bank"
        .TextMatrix(0, 7) = "Status"
        .TextMatrix(0, 8) = "Printed By"
        .TextMatrix(0, 9) = "Print#"
        .TextMatrix(0, 10) = "LayoutID"
    End With
End Sub

Private Sub cmdSearch_Click()
    Dim rs As ADODB.Recordset
    Dim sSql As String
    Dim r As Long
    sSql = "SELECT TOP 1000 r.RegisterID, r.VoucherNo, r.ChequeNo, r.PayeeName, r.Amount, r.ChequeDate, " & _
           "b.BankName, r.StatusCode, r.LastPrintedBy, r.PrintCount, r.LayoutID " & _
           "FROM CHEQUE_PRINT_REGISTER r LEFT JOIN BANK_MASTER b ON b.BankID=r.BankID WHERE r.CompanyID=" & CurrentChequeCompanyID()
    If Len(Trim$(txtVoucher.Text)) > 0 Then sSql = sSql & " AND r.VoucherNo LIKE '%" & SqlSafe(txtVoucher.Text) & "%'"
    If Len(Trim$(txtCheque.Text)) > 0 Then sSql = sSql & " AND r.ChequeNo LIKE '%" & SqlSafe(txtCheque.Text) & "%'"
    If Len(Trim$(txtParty.Text)) > 0 Then sSql = sSql & " AND r.PayeeName LIKE '%" & SqlSafe(txtParty.Text) & "%'"
    If Len(Trim$(txtAmount.Text)) > 0 And IsNumeric(txtAmount.Text) Then sSql = sSql & " AND r.Amount=" & Val(txtAmount.Text)
    If cboBank.ListIndex > 0 Then sSql = sSql & " AND r.BankID=" & cboBank.ItemData(cboBank.ListIndex)
    If cboStatus.ListIndex > 0 Then sSql = sSql & " AND r.StatusCode='" & SqlSafe(cboStatus.Text) & "'"
    If Len(Trim$(txtPrintedBy.Text)) > 0 Then sSql = sSql & " AND r.LastPrintedBy LIKE '%" & SqlSafe(txtPrintedBy.Text) & "%'"
    sSql = sSql & " AND r.ChequeDate>='" & Format$(dtFrom.Value, "yyyy-mm-dd") & "' AND r.ChequeDate<'" & Format$(DateAdd("d", 1, dtTo.Value), "yyyy-mm-dd") & "'"
    sSql = sSql & " ORDER BY r.ChequeDate DESC, r.RegisterID DESC"
    
    Set rs = ChqOpenRs(sSql)
    grd.Rows = 1
    r = 1
    Do While Not rs.EOF
        grd.Rows = r + 1
        grd.TextMatrix(r, 0) = NzStr(rs!RegisterID)
        grd.TextMatrix(r, 1) = NzStr(rs!VoucherNo)
        grd.TextMatrix(r, 2) = NzStr(rs!ChequeNo)
        grd.TextMatrix(r, 3) = NzStr(rs!PayeeName)
        grd.TextMatrix(r, 4) = Format$(NzDbl(rs!Amount), "#,##0.00")
        grd.TextMatrix(r, 5) = Format$(rs!ChequeDate, "dd-mmm-yyyy")
        grd.TextMatrix(r, 6) = NzStr(rs!BankName)
        grd.TextMatrix(r, 7) = NzStr(rs!StatusCode)
        grd.TextMatrix(r, 8) = NzStr(rs!LastPrintedBy)
        grd.TextMatrix(r, 9) = NzStr(rs!PrintCount)
        grd.TextMatrix(r, 10) = NzStr(rs!LayoutID)
        r = r + 1
        rs.MoveNext
    Loop
    rs.Close
End Sub

Private Sub cmdPreview_Click()
    Dim audit As New clsChequeAudit
    Dim frm As frmChequePrint
    If grd.Row < 1 Then Exit Sub
    If Not audit.HasPermission(CHQ_PERM_PREVIEW) Then
        ChqMsgError "No preview permission."
        Exit Sub
    End If
    Set frm = New frmChequePrint
    Call frm.InitFromVoucher(grd.TextMatrix(grd.Row, 1))
    frm.Show vbModal, Me
End Sub

Private Sub cmdExport_Click()
    Dim audit As New clsChequeAudit
    Dim i As Long, j As Long
    Dim sLine As String
    Dim nFile As Integer
    Dim sPath As String
    If Not audit.HasPermission(CHQ_PERM_EXPORT_PDF) Then
        ChqMsgError "No export permission."
        Exit Sub
    End If
    sPath = Environ$("TEMP") & "\ChequeRegister_" & Format$(Now, "yyyymmdd_hhnnss") & ".csv"
    nFile = FreeFile
    Open sPath For Output As #nFile
    For i = 0 To grd.Rows - 1
        sLine = ""
        For j = 0 To grd.Cols - 1
            If j > 0 Then sLine = sLine & ","
            sLine = sLine & """" & Replace$(grd.TextMatrix(i, j), """", """""") & """"
        Next j
        Print #nFile, sLine
    Next i
    Close #nFile
    ChqMsgInfo "Exported to:" & vbCrLf & sPath
End Sub

Private Sub cmdClose_Click()
    Unload Me
End Sub
