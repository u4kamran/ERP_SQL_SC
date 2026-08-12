VERSION 5.00
Begin VB.Form frmChequeCalibration 
   BorderStyle     =   1  'Fixed Single
   Caption         =   "Cheque Alignment Wizard"
   ClientHeight    =   4260
   ClientLeft      =   45
   ClientTop       =   390
   ClientWidth     =   7200
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   4260
   ScaleWidth      =   7200
   StartUpPosition =   2  'CenterScreen
   Begin VB.ComboBox cboPrinter 
      Height          =   315
      Left            =   1440
      Style           =   2  'Dropdown List
      TabIndex        =   12
      Top             =   240
      Width           =   4335
   End
   Begin VB.ComboBox cboLayout 
      Height          =   315
      Left            =   1440
      Style           =   2  'Dropdown List
      TabIndex        =   11
      Top             =   720
      Width           =   4335
   End
   Begin VB.TextBox txtLeft 
      Height          =   315
      Left            =   1440
      TabIndex        =   10
      Text            =   "0"
      Top             =   1440
      Width           =   975
   End
   Begin VB.TextBox txtRight 
      Height          =   315
      Left            =   3960
      TabIndex        =   9
      Text            =   "0"
      Top             =   1440
      Width           =   975
   End
   Begin VB.TextBox txtTop 
      Height          =   315
      Left            =   1440
      TabIndex        =   8
      Text            =   "0"
      Top             =   1920
      Width           =   975
   End
   Begin VB.TextBox txtBottom 
      Height          =   315
      Left            =   3960
      TabIndex        =   7
      Text            =   "0"
      Top             =   1920
      Width           =   975
   End
   Begin VB.CommandButton cmdNudgeL 
      Caption         =   "<"
      Height          =   315
      Left            =   2520
      TabIndex        =   6
      Top             =   1440
      Width           =   375
   End
   Begin VB.CommandButton cmdNudgeR 
      Caption         =   ">"
      Height          =   315
      Left            =   5040
      TabIndex        =   5
      Top             =   1440
      Width           =   375
   End
   Begin VB.CommandButton cmdNudgeU 
      Caption         =   "^"
      Height          =   315
      Left            =   2520
      TabIndex        =   4
      Top             =   1920
      Width           =   375
   End
   Begin VB.CommandButton cmdNudgeD 
      Caption         =   "v"
      Height          =   315
      Left            =   5040
      TabIndex        =   3
      Top             =   1920
      Width           =   375
   End
   Begin VB.CommandButton cmdTest 
      Caption         =   "Print &Test"
      Height          =   375
      Left            =   1440
      TabIndex        =   2
      Top             =   2640
      Width           =   1455
   End
   Begin VB.CommandButton cmdSave 
      Caption         =   "&Save Offsets"
      Height          =   375
      Left            =   3120
      TabIndex        =   1
      Top             =   2640
      Width           =   1455
   End
   Begin VB.CommandButton cmdClose 
      Cancel          =   -1  'True
      Caption         =   "&Close"
      Height          =   375
      Left            =   4800
      TabIndex        =   0
      Top             =   2640
      Width           =   1455
   End
   Begin VB.Label lblPrinter 
      Caption         =   "Printer"
      Height          =   255
      Left            =   240
      TabIndex        =   18
      Top             =   270
      Width           =   1095
   End
   Begin VB.Label lblLayout 
      Caption         =   "Layout"
      Height          =   255
      Left            =   240
      TabIndex        =   17
      Top             =   750
      Width           =   1095
   End
   Begin VB.Label lblLeft 
      Caption         =   "Left (mm)"
      Height          =   255
      Left            =   240
      TabIndex        =   16
      Top             =   1470
      Width           =   1095
   End
   Begin VB.Label lblRight 
      Caption         =   "Right (mm)"
      Height          =   255
      Left            =   2760
      TabIndex        =   15
      Top             =   1470
      Width           =   1095
   End
   Begin VB.Label lblTop 
      Caption         =   "Top (mm)"
      Height          =   255
      Left            =   240
      TabIndex        =   14
      Top             =   1950
      Width           =   1095
   End
   Begin VB.Label lblBottom 
      Caption         =   "Bottom (mm)"
      Height          =   255
      Left            =   2760
      TabIndex        =   13
      Top             =   1950
      Width           =   1095
   End
   Begin VB.Label lblHelp 
      Caption         =   "Print a test page, then nudge offsets until fields align with the physical cheque. Offsets are saved per user/printer/layout without editing the layout."
      Height          =   735
      Left            =   240
      TabIndex        =   19
      Top             =   3240
      Width           =   6615
   End
End
Attribute VB_Name = "frmChequeCalibration"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private m_Layout As clsLayoutManager
Private m_Engine As clsChequePrinter
Private m_Prn As clsPrinterManager
Private Const NUDGE As Double = 0.5

Private Sub Form_Load()
    Dim audit As New clsChequeAudit
    Dim rs As ADODB.Recordset
    If Not audit.HasPermission(CHQ_PERM_CALIBRATE) Then
        ChqMsgError "You do not have permission to calibrate printers."
        Unload Me
        Exit Sub
    End If
    Set m_Layout = New clsLayoutManager
    Set m_Engine = New clsChequePrinter
    Set m_Prn = New clsPrinterManager
    Call m_Prn.FillCombo(cboPrinter)
    
    cboLayout.Clear
    Set rs = ChqOpenRs("SELECT LayoutID, LayoutName FROM CHEQUE_LAYOUT_MASTER WHERE Active=1 ORDER BY LayoutName")
    Do While Not rs.EOF
        cboLayout.AddItem NzStr(rs!LayoutName)
        cboLayout.ItemData(cboLayout.NewIndex) = NzLng(rs!LayoutID)
        rs.MoveNext
    Loop
    rs.Close
    If cboLayout.ListCount > 0 Then cboLayout.ListIndex = 0
    If cboPrinter.ListCount > 0 Then cboPrinter.ListIndex = 0
End Sub

Private Sub cboLayout_Click()
    If cboLayout.ListIndex < 0 Then Exit Sub
    Call m_Layout.LoadLayout(cboLayout.ItemData(cboLayout.ListIndex))
    Call LoadOffsets
End Sub

Private Sub cboPrinter_Click()
    Call LoadOffsets
End Sub

Private Sub LoadOffsets()
    If cboLayout.ListIndex < 0 Or cboPrinter.ListIndex < 0 Then Exit Sub
    Call m_Layout.LoadCalibration(cboPrinter.Text, cboLayout.ItemData(cboLayout.ListIndex))
    txtLeft.Text = CStr(m_Layout.OffsetLeft)
    txtRight.Text = CStr(m_Layout.OffsetRight)
    txtTop.Text = CStr(m_Layout.OffsetTop)
    txtBottom.Text = CStr(m_Layout.OffsetBottom)
End Sub

Private Sub ApplyLocalOffsets()
    m_Layout.OffsetLeft = Val(txtLeft.Text)
    m_Layout.OffsetRight = Val(txtRight.Text)
    m_Layout.OffsetTop = Val(txtTop.Text)
    m_Layout.OffsetBottom = Val(txtBottom.Text)
End Sub

Private Sub cmdNudgeL_Click()
    txtLeft.Text = CStr(Val(txtLeft.Text) - NUDGE)
End Sub
Private Sub cmdNudgeR_Click()
    txtRight.Text = CStr(Val(txtRight.Text) - NUDGE)
End Sub
Private Sub cmdNudgeU_Click()
    txtTop.Text = CStr(Val(txtTop.Text) - NUDGE)
End Sub
Private Sub cmdNudgeD_Click()
    txtBottom.Text = CStr(Val(txtBottom.Text) - NUDGE)
End Sub

Private Sub cmdTest_Click()
    Call ApplyLocalOffsets
    Call m_Engine.LoadLayout(cboLayout.ItemData(cboLayout.ListIndex))
    m_Engine.Layout.OffsetLeft = Val(txtLeft.Text)
    m_Engine.Layout.OffsetRight = Val(txtRight.Text)
    m_Engine.Layout.OffsetTop = Val(txtTop.Text)
    m_Engine.Layout.OffsetBottom = Val(txtBottom.Text)
    Set m_Engine.ChequeData = New clsChequeData
    With m_Engine.ChequeData
        .PayeeName = "ALIGNMENT TEST PAYEE"
        .Amount = 1000
        .CurrencyCode = "PKR"
        .ChequeDate = Date
        .ChequeNo = "TEST"
        .VoucherNo = "TEST"
        .StatusCode = CHQ_STATUS_DRAFT
    End With
    m_Engine.PrinterName = cboPrinter.Text
    If m_Engine.PrintTestPage Then
        ChqMsgInfo "Test page printed. Adjust offsets and retry until aligned."
    Else
        ChqMsgError m_Engine.LastError
    End If
End Sub

Private Sub cmdSave_Click()
    Call ApplyLocalOffsets
    Call m_Layout.SaveCalibration(cboPrinter.Text, Val(txtLeft.Text), Val(txtRight.Text), _
                                  Val(txtTop.Text), Val(txtBottom.Text), cboLayout.ItemData(cboLayout.ListIndex))
    ChqMsgInfo "Offsets saved for this user / printer / layout."
End Sub

Private Sub cmdClose_Click()
    Unload Me
End Sub
