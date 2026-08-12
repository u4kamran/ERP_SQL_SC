VERSION 5.00
Object = "{5E9E78A0-531B-11CF-91F6-C2863C385E30}#1.0#0"; "MSFLXGRD.OCX"
Begin VB.Form frmChequeBatch 
   Caption         =   "Batch Cheque Printing"
   ClientHeight    =   7200
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   11000
   LinkTopic       =   "Form1"
   ScaleHeight     =   7200
   ScaleWidth      =   11000
   StartUpPosition =   2  'CenterScreen
   Begin VB.TextBox txtVouchers 
      Height          =   1455
      Left            =   120
      MultiLine       =   -1  'True
      ScrollBars      =   2  'Vertical
      TabIndex        =   5
      Top             =   480
      Width           =   10695
   End
   Begin VB.CommandButton cmdLoad 
      Caption         =   "&Load List"
      Height          =   375
      Left            =   120
      TabIndex        =   4
      Top             =   2040
      Width           =   1335
   End
   Begin VB.CommandButton cmdPrintAll 
      Caption         =   "&Print Selected"
      Height          =   375
      Left            =   1680
      TabIndex        =   3
      Top             =   2040
      Width           =   1575
   End
   Begin VB.CommandButton cmdClose 
      Cancel          =   -1  'True
      Caption         =   "&Close"
      Height          =   375
      Left            =   9480
      TabIndex        =   2
      Top             =   6600
      Width           =   1335
   End
   Begin MSFlexGridLib.MSFlexGrid grd 
      Height          =   3855
      Left            =   120
      TabIndex        =   1
      Top             =   2520
      Width           =   10695
      _ExtentX        =   18865
      _ExtentY        =   6800
      _Version        =   393216
      Cols            =   6
      FixedCols       =   0
      AllowUserResizing=   1
   End
   Begin VB.Label lblHelp 
      Caption         =   "Paste voucher numbers (one per line or comma-separated), then Load List and Print Selected."
      Height          =   255
      Left            =   120
      TabIndex        =   0
      Top             =   120
      Width           =   10695
   End
End
Attribute VB_Name = "frmChequeBatch"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Sub Form_Load()
    Dim audit As New clsChequeAudit
    If Not audit.HasPermission(CHQ_PERM_BATCH) Then
        ChqMsgError "You do not have permission for batch cheque printing."
        Unload Me
        Exit Sub
    End If
    With grd
        .Rows = 1: .Cols = 6
        .TextMatrix(0, 0) = "Sel"
        .TextMatrix(0, 1) = "Voucher"
        .TextMatrix(0, 2) = "Payee"
        .TextMatrix(0, 3) = "Amount"
        .TextMatrix(0, 4) = "Cheque#"
        .TextMatrix(0, 5) = "Status"
    End With
End Sub

Private Sub cmdLoad_Click()
    Dim raw As String
    Dim parts() As String
    Dim i As Long
    Dim s As String
    Dim d As clsChequeData
    Dim r As Long
    
    raw = Replace$(txtVouchers.Text, vbCrLf, ",")
    raw = Replace$(raw, vbLf, ",")
    raw = Replace$(raw, ";", ",")
    parts = Split(raw, ",")
    grd.Rows = 1
    r = 1
    For i = LBound(parts) To UBound(parts)
        s = Trim$(parts(i))
        If Len(s) = 0 Then GoTo NextItem
        Set d = New clsChequeData
        If d.LoadFromVoucher(s) Then
            grd.Rows = r + 1
            grd.TextMatrix(r, 0) = "Y"
            grd.TextMatrix(r, 1) = d.VoucherNo
            grd.TextMatrix(r, 2) = d.PayeeName
            grd.TextMatrix(r, 3) = Format$(d.Amount, "#,##0.00")
            grd.TextMatrix(r, 4) = d.ChequeNo
            grd.TextMatrix(r, 5) = d.StatusCode
            r = r + 1
        End If
NextItem:
    Next i
End Sub

Private Sub grd_DblClick()
    If grd.Row < 1 Then Exit Sub
    If grd.Col = 0 Then
        If grd.TextMatrix(grd.Row, 0) = "Y" Then
            grd.TextMatrix(grd.Row, 0) = "N"
        Else
            grd.TextMatrix(grd.Row, 0) = "Y"
        End If
    End If
End Sub

Private Sub cmdPrintAll_Click()
    Dim i As Long
    Dim eng As clsChequePrinter
    Dim ok As Long, fail As Long
    Dim bForce As Boolean
    Dim audit As New clsChequeAudit
    
    If Not audit.HasPermission(CHQ_PERM_PRINT) Then
        ChqMsgError "No print permission."
        Exit Sub
    End If
    
    For i = 1 To grd.Rows - 1
        If grd.TextMatrix(i, 0) <> "Y" Then GoTo NextRow
        Set eng = New clsChequePrinter
        If Not eng.PrepareFromVoucher(grd.TextMatrix(i, 1)) Then
            fail = fail + 1
            grd.TextMatrix(i, 5) = "ERR: " & eng.LastError
            GoTo NextRow
        End If
        bForce = False
        If eng.ChequeData.AlreadyPrinted Then
            If Not audit.HasPermission(CHQ_PERM_REPRINT) Then
                fail = fail + 1
                grd.TextMatrix(i, 5) = "Skip reprint"
                GoTo NextRow
            End If
            bForce = True
        End If
        If eng.PrintCheque(bForce) Then
            ok = ok + 1
            grd.TextMatrix(i, 5) = eng.ChequeData.StatusCode
        Else
            fail = fail + 1
            grd.TextMatrix(i, 5) = Left$(eng.LastError, 40)
        End If
NextRow:
    Next i
    ChqMsgInfo "Batch complete. Printed: " & ok & "  Failed/Skipped: " & fail
End Sub

Private Sub cmdClose_Click()
    Unload Me
End Sub
