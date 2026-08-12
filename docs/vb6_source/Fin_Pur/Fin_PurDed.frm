VERSION 5.00
Begin VB.Form Fin_PurDed 
   BackColor       =   &H00C0C0C0&
   BorderStyle     =   4  'Fixed ToolWindow
   Caption         =   "Abc Company Invoice"
   ClientHeight    =   2505
   ClientLeft      =   45
   ClientTop       =   285
   ClientWidth     =   6615
   ControlBox      =   0   'False
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   2505
   ScaleWidth      =   6615
   ShowInTaskbar   =   0   'False
   StartUpPosition =   1  'CenterOwner
   Begin VB.TextBox TxtOtherCharges 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   4905
      TabIndex        =   5
      Top             =   1200
      Width           =   1605
   End
   Begin VB.TextBox TxtCarriage 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   4905
      TabIndex        =   4
      Top             =   840
      Width           =   1605
   End
   Begin VB.TextBox TxtLoading 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   4905
      TabIndex        =   3
      Top             =   480
      Width           =   1605
   End
   Begin VB.TextBox TxtOtherDed 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   1605
      TabIndex        =   2
      Top             =   1200
      Width           =   1605
   End
   Begin VB.TextBox TxtClaim 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   1605
      TabIndex        =   1
      Top             =   840
      Width           =   1605
   End
   Begin VB.TextBox TxtDiscount 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   1605
      TabIndex        =   0
      Top             =   480
      Width           =   1605
   End
   Begin VB.CommandButton CmdClear 
      Caption         =   "Clea&r"
      CausesValidation=   0   'False
      Height          =   375
      Left            =   4245
      TabIndex        =   7
      Top             =   2055
      Width           =   1125
   End
   Begin VB.CommandButton CmdSave 
      Caption         =   "&Save"
      Height          =   375
      Left            =   3105
      TabIndex        =   6
      Top             =   2055
      Width           =   1125
   End
   Begin VB.CommandButton CmdClose 
      Caption         =   "&Close"
      Height          =   375
      Left            =   5490
      TabIndex        =   8
      Top             =   2055
      Width           =   1125
   End
   Begin VB.Label LblTotalCharges 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "0.00"
      ForeColor       =   &H00400000&
      Height          =   315
      Left            =   4905
      TabIndex        =   20
      Top             =   1575
      Width           =   1605
   End
   Begin VB.Label Label10 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Total Charges :"
      Height          =   195
      Left            =   3375
      TabIndex        =   19
      Top             =   1620
      Width           =   1470
   End
   Begin VB.Label LblTotalDed33 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Total Ded :"
      Height          =   195
      Left            =   810
      TabIndex        =   18
      Top             =   1620
      Width           =   720
   End
   Begin VB.Label Label8 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Loading/UnLoading:"
      Height          =   195
      Left            =   3375
      TabIndex        =   17
      Top             =   555
      Width           =   1470
   End
   Begin VB.Label Label7 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Carriage && Freight:"
      Height          =   195
      Left            =   3375
      TabIndex        =   16
      Top             =   870
      Width           =   1470
   End
   Begin VB.Label Label6 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Advance Tax :"
      Height          =   195
      Left            =   3375
      TabIndex        =   15
      Top             =   1260
      Width           =   1470
   End
   Begin VB.Label Label5 
      Alignment       =   2  'Center
      BackColor       =   &H00FCDABE&
      Caption         =   "Charges"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   345
      Left            =   3315
      TabIndex        =   14
      Top             =   75
      Width           =   3195
   End
   Begin VB.Label Label1 
      Alignment       =   2  'Center
      BackColor       =   &H00FCDABE&
      Caption         =   "Deduction"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   345
      Left            =   45
      TabIndex        =   13
      Top             =   75
      Width           =   3195
   End
   Begin VB.Label LblTotalDed 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "0.00"
      ForeColor       =   &H00400000&
      Height          =   315
      Left            =   1605
      TabIndex        =   12
      Top             =   1560
      Width           =   1605
   End
   Begin VB.Label Label4 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Other Ded :"
      Height          =   195
      Left            =   810
      TabIndex        =   11
      Top             =   1230
      Width           =   720
   End
   Begin VB.Label Label3 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Claim :"
      Height          =   195
      Left            =   810
      TabIndex        =   10
      Top             =   870
      Width           =   720
   End
   Begin VB.Label Label2 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Discount :"
      Height          =   195
      Left            =   810
      TabIndex        =   9
      Top             =   555
      Width           =   720
   End
End
Attribute VB_Name = "Fin_PurDed"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit
' Purchase
'Private tQty, tAmount As Double
Dim RsDummy As New ADODB.Recordset
Dim mUomID As Integer
Private mExclAmount, mTaxAmount, mInclAmount As Double
Private mSaleTaxRate As Single
'
Private Sub mTotals()
    LblTotalDed.Caption = Val(TxtDiscount) + Val(TxtClaim) + Val(TxtOtherDed)
    LblTotalCharges.Caption = Val(TxtCarriage) + Val(TxtLoading) + Val(TxtOtherCharges)
End Sub
Private Sub CmdClear_Click()
    Call clearform
End Sub
Private Sub cmdClose_Click()
    Unload Me
End Sub

Private Sub CmdSave_Click()
    Call mTotals
    Fin_PurM.HDiscount = TxtDiscount.Text
    Fin_PurM.HClaim = TxtClaim.Text
    Fin_PurM.HOtherDed = TxtOtherDed.Text
    Fin_PurM.HLoading = TxtCarriage.Text
    Fin_PurM.HCarriage = TxtLoading.Text
    Fin_PurM.HOtherCharges = TxtOtherCharges.Text
    Fin_PurM.LblDiscount.Caption = LblTotalDed
    Fin_PurM.LblCharges.Caption = LblTotalCharges
    Unload Me
End Sub

Private Sub CmdSave_GotFocus()
    Call mTotals
End Sub

Private Sub Form_KeyPress(KeyAscii As Integer)
Call EnterKeyEnable(KeyAscii)
''   If KeyAscii = 13 Then
''      KeyAscii = 0
''      SendKeys "{TAB}"
''   End If
End Sub
Private Function clearform()
   ' Clear Data Fields
    LblTotalDed.Caption = ""
    TxtDiscount.Text = ""
    TxtClaim.Text = ""
    TxtOtherDed.Text = ""
    LblTotalCharges.Caption = ""
    TxtCarriage.Text = ""
    TxtLoading.Text = ""
    TxtOtherCharges.Text = ""
End Function

Private Sub Form_Load(): Call FormDisplaySetting(Me)
    'Block by MKB 07 03 2024
    TxtDiscount.Text = Fin_PurM.HDiscount
    TxtClaim.Text = Fin_PurM.HClaim
    TxtOtherDed.Text = Fin_PurM.HOtherDed
    TxtCarriage.Text = Fin_PurM.HLoading
    TxtLoading.Text = Fin_PurM.HCarriage
    TxtOtherCharges.Text = Fin_PurM.HOtherCharges
    Call mTotals
End Sub
Private Sub TxtCarriage_Validate(Cancel As Boolean)
    Call mTotals
End Sub

Private Sub TxtClaim_Validate(Cancel As Boolean)
    Call mTotals
End Sub
Private Sub TxtDiscount_Validate(Cancel As Boolean)
    Call mTotals
End Sub

Private Sub TxtLoading_Validate(Cancel As Boolean)
    Call mTotals
End Sub

Private Sub TxtOtherCharges_Validate(Cancel As Boolean)
    Call mTotals
End Sub

Private Sub TxtOtherDed_Validate(Cancel As Boolean)
    Call mTotals
End Sub
