VERSION 5.00
Object = "{5E9E78A0-531B-11CF-91F6-C2863C385E30}#1.0#0"; "MSFLXGRD.OCX"
Begin VB.Form frmChequeHistory 
   Caption         =   "Cheque Print History / Audit"
   ClientHeight    =   7200
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   12000
   LinkTopic       =   "Form1"
   ScaleHeight     =   7200
   ScaleWidth      =   12000
   StartUpPosition =   2  'CenterScreen
   Begin VB.TextBox txtChequeNo 
      Height          =   315
      Left            =   1200
      TabIndex        =   5
      Top             =   240
      Width           =   1695
   End
   Begin VB.TextBox txtVoucherNo 
      Height          =   315
      Left            =   4200
      TabIndex        =   4
      Top             =   240
      Width           =   1695
   End
   Begin VB.CommandButton cmdSearch 
      Caption         =   "&Search"
      Height          =   375
      Left            =   6120
      TabIndex        =   3
      Top             =   216
      Width           =   1215
   End
   Begin VB.CommandButton cmdClose 
      Cancel          =   -1  'True
      Caption         =   "&Close"
      Height          =   375
      Left            =   10560
      TabIndex        =   2
      Top             =   6600
      Width           =   1215
   End
   Begin MSFlexGridLib.MSFlexGrid grd 
      Height          =   5535
      Left            =   120
      TabIndex        =   1
      Top             =   840
      Width           =   11655
      _ExtentX        =   20558
      _ExtentY        =   9763
      _Version        =   393216
      Cols            =   10
      FixedCols       =   0
      AllowUserResizing=   1
   End
   Begin VB.Label lblChq 
      Caption         =   "Cheque No"
      Height          =   255
      Left            =   120
      TabIndex        =   0
      Top             =   270
      Width           =   975
   End
   Begin VB.Label lblVch 
      Caption         =   "Voucher No"
      Height          =   255
      Left            =   3120
      TabIndex        =   6
      Top             =   270
      Width           =   975
   End
End
Attribute VB_Name = "frmChequeHistory"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Sub Form_Load()
    Dim audit As New clsChequeAudit
    If Not audit.HasPermission(CHQ_PERM_HISTORY) Then
        ChqMsgError "No permission to view cheque history."
        Unload Me
        Exit Sub
    End If
    With grd
        .Rows = 1
        .Cols = 10
        .TextMatrix(0, 0) = "AuditID"
        .TextMatrix(0, 1) = "Action"
        .TextMatrix(0, 2) = "Voucher"
        .TextMatrix(0, 3) = "Cheque#"
        .TextMatrix(0, 4) = "Printed By"
        .TextMatrix(0, 5) = "Date"
        .TextMatrix(0, 6) = "Time"
        .TextMatrix(0, 7) = "Printer"
        .TextMatrix(0, 8) = "Computer"
        .TextMatrix(0, 9) = "Reprint?"
    End With
    Call cmdSearch_Click
End Sub

Private Sub cmdSearch_Click()
    Dim rs As ADODB.Recordset
    Dim sSql As String
    Dim r As Long
    sSql = "SELECT TOP 500 AuditID, ActionCode, VoucherNo, ChequeNo, PrintedBy, PrintedDate, PrintedTime, PrinterName, ComputerName, IsReprint " & _
           "FROM CHEQUE_PRINT_AUDIT WHERE 1=1"
    If Len(Trim$(txtChequeNo.Text)) > 0 Then sSql = sSql & " AND ChequeNo LIKE '%" & SqlSafe(txtChequeNo.Text) & "%'"
    If Len(Trim$(txtVoucherNo.Text)) > 0 Then sSql = sSql & " AND VoucherNo LIKE '%" & SqlSafe(txtVoucherNo.Text) & "%'"
    sSql = sSql & " ORDER BY PrintedDate DESC, AuditID DESC"
    Set rs = ChqOpenRs(sSql)
    grd.Rows = 1
    r = 1
    Do While Not rs.EOF
        grd.Rows = r + 1
        grd.TextMatrix(r, 0) = NzStr(rs!AuditID)
        grd.TextMatrix(r, 1) = NzStr(rs!ActionCode)
        grd.TextMatrix(r, 2) = NzStr(rs!VoucherNo)
        grd.TextMatrix(r, 3) = NzStr(rs!ChequeNo)
        grd.TextMatrix(r, 4) = NzStr(rs!PrintedBy)
        grd.TextMatrix(r, 5) = Format$(rs!PrintedDate, "dd-mmm-yyyy")
        grd.TextMatrix(r, 6) = NzStr(rs!PrintedTime)
        grd.TextMatrix(r, 7) = NzStr(rs!PrinterName)
        grd.TextMatrix(r, 8) = NzStr(rs!ComputerName)
        grd.TextMatrix(r, 9) = IIf(NzBool(rs!IsReprint), "Yes", "No")
        r = r + 1
        rs.MoveNext
    Loop
    rs.Close
End Sub

Private Sub cmdClose_Click()
    Unload Me
End Sub
