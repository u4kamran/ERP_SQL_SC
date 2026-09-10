VERSION 5.00
Object = "{C0A63B80-4B21-11D3-BD95-D426EF2C7949}#1.0#0"; "Vsflex7L.ocx"
Object = "{86CF1D34-0C5F-11D2-A9FC-0000F8754DA1}#2.0#0"; "MSCOMCT2.OCX"
Begin VB.Form Fin_PurD_JSON 
   BackColor       =   &H00C0C0C0&
   BorderStyle     =   4  'Fixed ToolWindow
   Caption         =   "Abc Company"
   ClientHeight    =   8760
   ClientLeft      =   45
   ClientTop       =   285
   ClientWidth     =   8400
   ControlBox      =   0   'False
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   8760
   ScaleWidth      =   8400
   ShowInTaskbar   =   0   'False
   StartUpPosition =   1  'CenterOwner
   Begin VB.TextBox txtCoID 
      Height          =   315
      Left            =   3375
      TabIndex        =   28
      Top             =   3465
      Width           =   1605
   End
   Begin VB.TextBox txtNetCost 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      MaxLength       =   12
      TabIndex        =   62
      Top             =   2025
      Width           =   1605
   End
   Begin VB.TextBox txtOffInvDiscAmt 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   6690
      MaxLength       =   12
      TabIndex        =   27
      Top             =   3555
      Width           =   1650
   End
   Begin VB.TextBox TxtOffInvDiscPer 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      MaxLength       =   5
      TabIndex        =   57
      Top             =   3150
      Width           =   1605
   End
   Begin VB.TextBox txtMRP 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      Locked          =   -1  'True
      MaxLength       =   5
      TabIndex        =   18
      Top             =   2400
      Width           =   1605
   End
   Begin VB.TextBox txtNoOf 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   1545
      Locked          =   -1  'True
      MaxLength       =   10
      TabIndex        =   47
      Text            =   "5"
      Top             =   8295
      Width           =   1020
   End
   Begin VB.TextBox txtPQty 
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   3375
      TabIndex        =   8
      Top             =   1680
      Width           =   1605
   End
   Begin VB.TextBox TxtsRemarks 
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      MaxLength       =   10
      TabIndex        =   24
      Top             =   3885
      Width           =   1605
   End
   Begin VB.TextBox Text1 
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   3375
      TabIndex        =   4
      Top             =   2400
      Width           =   1605
   End
   Begin VB.TextBox txtUnit 
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   3375
      TabIndex        =   6
      Top             =   1335
      Width           =   1605
   End
   Begin VB.TextBox TxtPRate 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   3375
      MaxLength       =   12
      TabIndex        =   10
      Top             =   2040
      Width           =   1605
   End
   Begin VB.TextBox txtBarcode 
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   3375
      TabIndex        =   2
      Top             =   2775
      Width           =   1605
   End
   Begin VB.TextBox TxtStaxRate 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      MaxLength       =   5
      TabIndex        =   22
      Top             =   3540
      Width           =   1605
   End
   Begin VB.TextBox txtDiscAmt 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   6690
      MaxLength       =   12
      TabIndex        =   25
      Top             =   2040
      Width           =   1650
   End
   Begin VB.TextBox txtDiscPer 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      MaxLength       =   5
      TabIndex        =   20
      Top             =   2760
      Width           =   1605
   End
   Begin VB.CommandButton CmdClose 
      Caption         =   "&Close"
      Height          =   375
      Left            =   7215
      TabIndex        =   35
      Top             =   4515
      Width           =   1125
   End
   Begin VB.CommandButton CmdSave 
      Caption         =   "&Save"
      Height          =   375
      Left            =   2640
      TabIndex        =   30
      Top             =   4515
      Width           =   1125
   End
   Begin VB.CommandButton CmdClear 
      Caption         =   "Clea&r"
      CausesValidation=   0   'False
      Height          =   375
      Left            =   3780
      TabIndex        =   32
      Top             =   4515
      Width           =   1125
   End
   Begin VB.CommandButton CmdItem 
      Caption         =   "&Item"
      Height          =   375
      Left            =   4920
      TabIndex        =   33
      Top             =   4515
      Width           =   1125
   End
   Begin VB.CommandButton CmdBalance 
      Caption         =   "Balance"
      Height          =   375
      Left            =   6075
      TabIndex        =   34
      Top             =   4515
      Width           =   1125
   End
   Begin VB.CommandButton cmdImportExcel 
      Caption         =   "Import From Excel"
      Height          =   375
      Left            =   45
      TabIndex        =   63
      ToolTipText     =   "Import purchase detail rows from SupplierID*.xlsx (Sheet 2)"
      Top             =   4515
      Width           =   1395
   End
   Begin VB.CommandButton cmdEditInExcel 
      Caption         =   "Edit in Excel"
      Height          =   375
      Left            =   1485
      TabIndex        =   64
      ToolTipText     =   "Update Qty/Rate in SupplierID*.xlsx Sheet 1 for current Manual ID"
      Top             =   4515
      Width           =   1125
   End
   Begin VB.TextBox txtBarcodeWS 
      Height          =   315
      Left            =   3375
      TabIndex        =   0
      Top             =   3150
      Width           =   1605
   End
   Begin VB.TextBox TxtStaxAmount 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   6690
      MaxLength       =   12
      TabIndex        =   26
      Top             =   2820
      Width           =   1650
   End
   Begin VB.TextBox TxtRate 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      MaxLength       =   12
      TabIndex        =   16
      Top             =   1680
      Width           =   1605
   End
   Begin VB.TextBox TxtQty 
      Alignment       =   1  'Right Justify
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      MaxLength       =   12
      TabIndex        =   14
      Top             =   1335
      Width           =   1605
   End
   Begin VB.TextBox TxtID 
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   360
      Left            =   960
      TabIndex        =   12
      Top             =   990
      Width           =   1605
   End
   Begin VSFlex7LCtl.VSFlexGrid grd 
      Height          =   3375
      Index           =   0
      Left            =   0
      TabIndex        =   46
      Top             =   4905
      Width           =   8265
      _cx             =   14579
      _cy             =   5953
      _ConvInfo       =   1
      Appearance      =   1
      BorderStyle     =   1
      Enabled         =   -1  'True
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Calibri"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      MousePointer    =   0
      BackColor       =   16248808
      ForeColor       =   0
      BackColorFixed  =   -2147483633
      ForeColorFixed  =   -2147483630
      BackColorSel    =   -2147483635
      ForeColorSel    =   -2147483634
      BackColorBkg    =   14333592
      BackColorAlternate=   14799560
      GridColor       =   -2147483633
      GridColorFixed  =   -2147483632
      TreeColor       =   -2147483632
      FloodColor      =   192
      SheetBorder     =   -2147483642
      FocusRect       =   3
      HighLight       =   1
      AllowSelection  =   -1  'True
      AllowBigSelection=   -1  'True
      AllowUserResizing=   1
      SelectionMode   =   0
      GridLines       =   1
      GridLinesFixed  =   2
      GridLineWidth   =   1
      Rows            =   2
      Cols            =   3
      FixedRows       =   1
      FixedCols       =   0
      RowHeightMin    =   0
      RowHeightMax    =   0
      ColWidthMin     =   0
      ColWidthMax     =   0
      ExtendLastCol   =   0   'False
      FormatString    =   $"Fin_PurD_JSON.frx":0000
      ScrollTrack     =   0   'False
      ScrollBars      =   3
      ScrollTips      =   0   'False
      MergeCells      =   0
      MergeCompare    =   0
      AutoResize      =   -1  'True
      AutoSizeMode    =   0
      AutoSearch      =   0
      AutoSearchDelay =   2
      MultiTotals     =   -1  'True
      SubtotalPosition=   1
      OutlineBar      =   0
      OutlineCol      =   0
      Ellipsis        =   0
      ExplorerBar     =   5
      PicturesOver    =   0   'False
      FillStyle       =   0
      RightToLeft     =   0   'False
      PictureType     =   0
      TabBehavior     =   1
      OwnerDraw       =   0
      Editable        =   2
      ShowComboButton =   -1  'True
      WordWrap        =   -1  'True
      TextStyle       =   0
      TextStyleFixed  =   0
      OleDragMode     =   0
      OleDropMode     =   0
      ComboSearch     =   3
      AutoSizeMouse   =   -1  'True
      FrozenRows      =   0
      FrozenCols      =   0
      AllowUserFreezing=   3
      BackColorFrozen =   0
      ForeColorFrozen =   0
      WallPaperAlignment=   9
   End
   Begin MSComCtl2.DTPicker TxtExpDate 
      Height          =   315
      Left            =   3375
      TabIndex        =   29
      Top             =   3780
      Width           =   1605
      _ExtentX        =   2831
      _ExtentY        =   556
      _Version        =   393216
      Format          =   157679617
      CurrentDate     =   36524
   End
   Begin VB.Label lblCoTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Item Title"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   330
      Left            =   3375
      TabIndex        =   65
      Top             =   4140
      Width           =   2220
   End
   Begin VB.Label Label26 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Co ID :"
      Height          =   195
      Left            =   2835
      TabIndex        =   31
      Top             =   3525
      Width           =   495
   End
   Begin VB.Label Label25 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Exp Date :"
      Height          =   195
      Left            =   2580
      TabIndex        =   67
      Top             =   3840
      Width           =   750
   End
   Begin VB.Label Label24 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Net Cost :"
      Height          =   195
      Left            =   210
      TabIndex        =   66
      Top             =   2115
      Width           =   705
   End
   Begin VB.Label LblOffInvIncludedAmt 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "0.00"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   360
      Left            =   6690
      TabIndex        =   61
      Top             =   3195
      Width           =   1650
   End
   Begin VB.Label Label23 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Included Amount :"
      Height          =   195
      Left            =   5280
      TabIndex        =   60
      Top             =   3285
      Width           =   1380
   End
   Begin VB.Label Label22 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Off InvDisc :"
      Height          =   195
      Left            =   5775
      TabIndex        =   59
      Top             =   3645
      Width           =   885
   End
   Begin VB.Label Label21 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Disc% Off  :"
      Height          =   195
      Left            =   90
      TabIndex        =   58
      Top             =   3240
      Width           =   825
   End
   Begin VB.Label lblProfitPer 
      Alignment       =   2  'Center
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "%"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   15
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H000000FF&
      Height          =   495
      Left            =   45
      TabIndex        =   56
      Top             =   105
      Visible         =   0   'False
      Width           =   1500
   End
   Begin VB.Label Label20 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "M.R.P :"
      Height          =   195
      Left            =   375
      TabIndex        =   17
      Top             =   2490
      Width           =   540
   End
   Begin VB.Label lblSale 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "0.00"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   360
      Left            =   4995
      TabIndex        =   45
      Top             =   1335
      Width           =   1110
   End
   Begin VB.Label lblStock 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "0"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   360
      Left            =   4995
      TabIndex        =   55
      Top             =   1710
      Width           =   1110
   End
   Begin VB.Label Label14 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&Unit :"
      Height          =   195
      Left            =   2655
      TabIndex        =   5
      Top             =   1418
      Width           =   675
   End
   Begin VB.Label Label15 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Qua&ntity :"
      Height          =   195
      Left            =   2655
      TabIndex        =   7
      Top             =   1763
      Width           =   675
   End
   Begin VB.Label Label16 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "R&ate :"
      Height          =   195
      Left            =   2895
      TabIndex        =   9
      Top             =   2130
      Width           =   435
   End
   Begin VB.Label Label12 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&Manual :"
      Height          =   195
      Left            =   2655
      TabIndex        =   3
      Top             =   2483
      Width           =   675
   End
   Begin VB.Label Label13 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&Barcode :"
      Height          =   195
      Left            =   2655
      TabIndex        =   1
      Top             =   2858
      Width           =   675
   End
   Begin VB.Label Label8 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "G Amt :"
      Height          =   195
      Left            =   6135
      TabIndex        =   53
      Top             =   1785
      Width           =   525
   End
   Begin VB.Label Label7 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Net Amount :"
      Height          =   195
      Left            =   5730
      TabIndex        =   52
      Top             =   4020
      Width           =   930
   End
   Begin VB.Label Label10 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Sales Tax Amount :"
      Height          =   195
      Left            =   5280
      TabIndex        =   51
      Top             =   2910
      Width           =   1380
   End
   Begin VB.Label Label17 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "TO + On InvDisc :"
      Height          =   195
      Left            =   5370
      TabIndex        =   50
      Top             =   2130
      Width           =   1290
   End
   Begin VB.Label Label18 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Excluded Amount :"
      Height          =   195
      Left            =   5280
      TabIndex        =   49
      Top             =   2513
      Width           =   1380
   End
   Begin VB.Label Label19 
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "No of Pur Trans :"
      Height          =   195
      Left            =   195
      TabIndex        =   48
      Top             =   8385
      Width           =   1215
   End
   Begin VB.Label lblExcludAmt 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "0.00"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   360
      Left            =   6690
      TabIndex        =   44
      Top             =   2430
      Width           =   1650
   End
   Begin VB.Label Label5 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "S-&Tax % :"
      Height          =   195
      Left            =   240
      TabIndex        =   21
      Top             =   3630
      Width           =   675
   End
   Begin VB.Label Label11 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Disc% On :"
      Height          =   195
      Left            =   135
      TabIndex        =   19
      Top             =   2850
      Width           =   780
   End
   Begin VB.Label Label9 
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Sub Title :"
      Height          =   195
      Left            =   1740
      TabIndex        =   43
      Top             =   585
      Width           =   720
   End
   Begin VB.Label Label2 
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Main Title :"
      Height          =   195
      Left            =   1680
      TabIndex        =   42
      Top             =   180
      Width           =   780
   End
   Begin VB.Label LblMainTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Main Title"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   330
      Left            =   2535
      TabIndex        =   41
      Top             =   105
      Width           =   5820
   End
   Begin VB.Label LblSubTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "SubTitle"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   330
      Left            =   2535
      TabIndex        =   40
      Top             =   525
      Width           =   5820
   End
   Begin VB.Label LblIncludedAmount 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "0.00"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   360
      Left            =   6690
      TabIndex        =   39
      Top             =   3930
      Width           =   1650
   End
   Begin VB.Label Label1 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Remar&ks :"
      Height          =   195
      Left            =   135
      TabIndex        =   23
      Top             =   3975
      Width           =   780
   End
   Begin VB.Label TxtAmount 
      Alignment       =   1  'Right Justify
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "0.00"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   360
      Left            =   6690
      TabIndex        =   38
      Top             =   1710
      Width           =   1650
   End
   Begin VB.Label TxtUomTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Unit of Measurement"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   360
      Left            =   6690
      TabIndex        =   37
      Top             =   1335
      Width           =   1650
   End
   Begin VB.Label Label4 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "TP Rat&e :"
      Height          =   195
      Left            =   225
      TabIndex        =   15
      Top             =   1770
      Width           =   690
   End
   Begin VB.Label Label3 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&Quantity :"
      Height          =   195
      Left            =   135
      TabIndex        =   13
      Top             =   1425
      Width           =   780
   End
   Begin VB.Label LblItem 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&Item ID :"
      Height          =   195
      Left            =   135
      TabIndex        =   11
      Top             =   1080
      Width           =   780
   End
   Begin VB.Label TxtTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Item Title"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00400000&
      Height          =   330
      Left            =   2805
      TabIndex        =   36
      Top             =   960
      Width           =   5550
   End
   Begin VB.Label Label6 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "UOM :"
      Height          =   195
      Left            =   5280
      TabIndex        =   54
      Top             =   1365
      Width           =   1380
   End
End
Attribute VB_Name = "Fin_PurD_JSON"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit
'Private tQty, tAmount As Double
Private mPurAmount, mTaxAmount, mDiscAmount, mDiscOffInvAmt, mOffInvIncludedAmt, mInclAmount, mNetCost As Double
Private mSaleTaxRate As Single
Private RsDummy, RsTmp As New ADODB.Recordset
Private mUomID, mEditRowID  As Integer
'
Private Sub Calc_Rate()
On Error GoTo TrapError
    If Val(TxtRate) = 0 And cAudit = 0 Then
        MsgBox "Invalid:  Please enter Rate ...  ", vbInformation, "Purchase Receipt"
        Exit Sub
    End If
    If Val(TxtQty) = 0 Then
        MsgBox "Invalid:  Please enter Quantity ...  ", vbInformation, "Purchase Receipt"
        Exit Sub
    End If
    'mPurAmount = Int(Val(TxtRate) * Val(TxtQty) + 0.5)
    mPurAmount = (Val(TxtRate) * Val(TxtQty))
    mTaxAmount = 0
    TxtAmount.Caption = Format(mPurAmount, "#########.00")
    
    If Val(TxtRate) <> 0 Then
        If Val(txtDiscPer) > 0 And mPurAmount <> 0 Then
        'mDiscAmount = ((mPurAmount + mTaxAmount) * Val(txtDiscPer) / 100)
            
            'tmp close KAM
           ' mDiscAmount = ((mPurAmount * Val(txtDiscPer) / 100))
             mDiscAmount = Val(txtDiscAmt)
             txtDiscPer = Format((Val(txtDiscAmt) / Val(mPurAmount) * 100), "#########.#0")
            
        Else
            mDiscAmount = Val(txtDiscAmt)
            txtDiscPer = Format((Val(txtDiscAmt) / Val(mPurAmount) * 100), "#########.#0")
        End If
        If Val(txtDiscPer) = 0 And mPurAmount <> 0 Then
            'txtDiscPer.Text = (Val(txtDiscAmt.Text) / mPurAmount) * 100
        End If
    End If
    
    
    'Stax Calculations Temporary Disable
    If Val(TxtRate) <> 0 Then
      If Val(TxtStaxRate) > 0 And mPurAmount <> 0 Then
          'mTaxAmount = Int(mPurAmount * Val(TxtStaxRate) / 100 + 0.5)
          'gross amt - discount
'           TxtStaxRate = Abs(Val(TxtStaxAmount) / Val(mPurAmount) * 100)
           'KAM
          'mTaxAmount = ((mPurAmount - mDiscAmount) * Val(TxtStaxRate) / 100)
          mTaxAmount = Format(Val(TxtStaxAmount), "#########.#0")
'
      Else
          mTaxAmount = Format(Val(TxtStaxAmount), "#########.#0")
'          TxtStaxRate = Abs(Val(TxtStaxAmount) / Val(mPurAmount) * 100)
      End If
    End If
    'End Tax Calcualation
    
    'Off Invoice Discount Calculation
    If Val(TxtRate) <> 0 Then
        If Val(TxtOffInvDiscPer) > 0 And mPurAmount <> 0 Then
        'mDiscAmount = ((mPurAmount + mTaxAmount) * Val(txtDiscPer) / 100)
            
            'tmp close KAM
           ' mDiscAmount = ((mPurAmount * Val(txtDiscPer) / 100))
             mDiscOffInvAmt = Format(Val(txtOffInvDiscAmt), "#########.#0")
             TxtOffInvDiscPer = Format((Val(txtOffInvDiscAmt) / Val(mPurAmount) * 100), "#########.#0")
            
        Else
            mDiscOffInvAmt = Format(Val(txtOffInvDiscAmt), "#########.#0")
            TxtOffInvDiscPer = Format((Val(txtOffInvDiscAmt) / Val(mPurAmount) * 100), "#########.#0")
        End If
        If Val(txtDiscPer) = 0 And mPurAmount <> 0 Then
            'txtDiscPer.Text = (Val(txtDiscAmt.Text) / mPurAmount) * 100
        End If
    End If
    
    
    '
'    TxtStaxAmount.Text = Format(mTaxAmount, "#########.#0")
'    txtDiscAmt.Text = Format(mDiscAmount, "#########.#0")

    
    
    
    mInclAmount = mPurAmount + mTaxAmount - mDiscAmount
    
    
    
    lblExcludAmt = Format(mPurAmount - mDiscAmount, "#########.#0")
    
    mOffInvIncludedAmt = Format(CDbl(lblExcludAmt) + mTaxAmount, "#########.#0")
    
    LblOffInvIncludedAmt = Format(mOffInvIncludedAmt, "#########.#0")
    
    LblIncludedAmount.Caption = Format(mInclAmount, "#########.00") - mDiscOffInvAmt
    
    If mPurAmount > 0 Then
        txtNetCost.Text = Format(((mPurAmount - mDiscAmount - mDiscOffInvAmt) / Val(TxtQty)), "#########.00")
        
    End If
    
    
    
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub
Private Sub PUpdateBalance()
On Error GoTo TrapError
   Dim nCnt As Integer
   Dim nQty As Double
   Dim nAmount As Double
   Dim nStax, nStaxPer As Double
   Dim nDiscount As Double
   Dim nOffInvDiscAmt As Double
   Dim nIncludedAmount As Double
   '
   For nCnt = 1 To max_entries
      Fin_PurM_JSON.VGrid.Row = nCnt
      Fin_PurM_JSON.VGrid.Col = 3
      nQty = nQty + CDbl(Fin_PurM_JSON.VGrid.Text & "0")
      'amount
      Fin_PurM_JSON.VGrid.Col = 5
      nAmount = nAmount + CDbl(Fin_PurM_JSON.VGrid.Text & "0")
      
      'sales tax per
      Fin_PurM_JSON.VGrid.Col = 6
      nStaxPer = CDbl(Fin_PurM_JSON.VGrid.Text & "0")
      
      
      'sales tax
      Fin_PurM_JSON.VGrid.Col = 7
      nStax = nStax + CDbl(Fin_PurM_JSON.VGrid.Text & "0")

      'Discount
      Fin_PurM_JSON.VGrid.Col = 9
      nDiscount = nDiscount + CDbl(Fin_PurM_JSON.VGrid.Text & "0")
      
      'Discount Off Invoice
      
      Fin_PurM_JSON.VGrid.Col = 11
      nOffInvDiscAmt = nOffInvDiscAmt + CDbl(Fin_PurM_JSON.VGrid.Text & "0")
      
      'Included Amount
      Fin_PurM_JSON.VGrid.Col = 12
      nIncludedAmount = nIncludedAmount + CDbl(Fin_PurM_JSON.VGrid.Text & "0")
      
   Next
   
      Fin_PurM_JSON.mQty.Caption = Format(nQty, "##,##0.00")
      Fin_PurM_JSON.mAmount.Caption = Format(nAmount, "##,##0.00")
      ' other two columns ?
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub
Private Sub CmdDelete_Click()
On Error GoTo TrapError
     Screen.MousePointer = vbHourglass
     Screen.MousePointer = vbDefault
     Call clearform
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub cmdPrint_Click()
'Call Calc_TB_Month
End Sub


Private Sub CmdBalance_Click()
On Error GoTo TrapError

    BalanceInv.Show vbModal, Me
    
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub CmdItem_Click()
On Error GoTo TrapError
    With Fin_Item
        .txtBarcodeID = txtBarcode.Text
        .txtManualID = Text1.Text
        .TxtID.Text = TxtID.Text
'        .TxtCost_Price.SetFocus
'        .txtManualID_Validate (False)
    End With
    
    Fin_Item.Show vbModal, Me
     Call TxtID_Validate(False)
     
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub CmdSave_Click()
On Error GoTo TrapError
    Dim iCounter    As Integer
    '
    If Val(TxtID) = 0 Then
        TxtID.SetFocus
        Exit Sub
    End If
    'Temp block the code
'    If Val(TxtRate) = 0 And cAudit = 0 Then
'        MsgBox "Invalid:  Please enter Rate ...  ", vbInformation, "Production Receipt"
'        TxtRate.SetFocus
'        Exit Sub
'    End If
    If Val(TxtQty) = 0 Then
        MsgBox "Invalid:  Please enter Quantity ...  ", vbInformation, "Production Receipt"
        TxtQty.SetFocus
        Exit Sub
    End If
   
    If txtCoID.Text = "" Then
        MsgBox "Invalid:  Please enter Company ID ...  ", vbInformation, "Production Receipt"
        txtCoID.SetFocus
        Exit Sub
    End If
   
       
        
        
        If Not Val(TxtID) < 0 Then
            SQL = "select * from FIN_ITEM where item_id=" & Val(TxtID)
            Set RsOld = FetchAll(SQL)
            If Not (RsOld.EOF And RsOld.BOF) Then
            
            End If
            
        End If
        
        
        
    With Cmd
'        MsgBox Rs!Inv_id
        .ActiveConnection = Con
        '.CommandText = "update fin_item set disc_p1 = " & CDbl(txtMRP.Text) & _
                        " where item_ID = " & CDbl(TxtID.Text)
        .CommandText = "update fin_item set disc_p1 = " & CDbl(txtMRP.Text) & " , STAX_REG = " & Val(TxtStaxRate) & " , oamt1 = " & Format(Val(TxtStaxAmount) / Val(TxtQty), "#######.00") & _
                        " , camt1 = " & Format((Val(TxtAmount) - Val(txtDiscAmt) - Val(txtOffInvDiscAmt)) / Val(TxtQty), "#######.00") & _
                        " , cqty1 = " & Format(CDbl(TxtRate.Text), "#######.00") & _
                        " , co_id = " & txtCoID.Text & _
                        " where item_ID = " & CDbl(TxtID.Text) '& " and STAX_REG = " & Val(TxtStaxRate) & " and oamt1 = " & Val(TxtStaxAmount)


        Debug.Print .CommandText
        .Execute
    End With
        
        If Not Val(TxtID) < 0 Then
            SQL = "select * from FIN_ITEM where item_id=" & Val(TxtID)
            Set Rs = FetchAll(SQL)
            If Not (Rs.EOF And Rs.BOF) Then
'                Rs!disc_p1 = CDbl(txtMRP.Text)
'                Rs!STAX_REG = Val(TxtStaxRate)
'                Rs!oamt1 = Format(Val(TxtStaxAmount) / Val(TxtQty), "#######.00")
'                Rs!camt1 = Format((Val(TxtAmount) - Val(txtDiscAmt) - Val(txtOffInvDiscAmt)) / Val(TxtQty), "#######.00")
'                Rs!cqty1 = Format(CDbl(TxtRate.Text), "#######.00")
'
'                Rs.Update
            End If
        End If
        
        Call SaveLogData("FIN_PUR_D", Rs, RsOld, RsOld!Item_ID, RsOld!manualid)
        
        RsOld.Close
        Rs.Close

    
    
'    Call SaveLogData("PUR_ITEM", Rs, RsOld, RsOld!Item_ID, RsOld!manualid)
    
    ' Check Duplicate item
    'IF CONDITION ADD BY MKB
    'If mEditRowID > 0 Then
    If lEdit = False Then
        With Fin_PurM_JSON.VGrid
                'Dim iCounter As Integer
                iCounter = 0
                Do While iCounter + 1 <> .Rows
                    .Row = iCounter + 1
                    .Col = 1
                    If Val(.Text) = Val(TxtID) Then
                        'MsgBox "meditrowid = " & mEditRowID & "   icounter +1 = " & iCounter + 1
                        'IF CONDITION CLOSE BY MKB
                        'If iCounter + 1 <> mEditRowID Then
                            MsgBox "Duplicate: Item ID Already Exists .... ", vbInformation
                            Exit Sub
                        'End If
                    End If
                     iCounter = iCounter + 1
                Loop
        End With
    End If
    '
    With Fin_PurM_JSON.VGrid
        If lEdit = False Then
            .Row = nCounter
        Else
            .Row = mEditRowID
        End If
        
        .CellAlignment = 1
        .Col = 1
        .Text = " " & TxtID.Text
        .Col = 2
        .Text = " " & Trim(TxtTitle.Caption)
        '
        .Col = 3
        .CellAlignment = 6
        .Text = Format(Val(TxtQty), "#########.#0")
        '
        .Col = 4
        .CellAlignment = 6
        .Text = Format(Val(TxtRate), "#########.#0")
        '
        .Col = 5
        .CellAlignment = 6
        .Text = Format(Val(TxtRate) * Val(TxtQty), "#########.#0")
        'Stax %
        .Col = 6
        .CellAlignment = 6
        .Text = Format(Val(TxtStaxRate), "#########.#0")
        'Stax amount
        .Col = 7
        .CellAlignment = 6
        .Text = Format(Val(TxtStaxAmount), "#########.#0")
        'Discount
        .Col = 8
        .CellAlignment = 6
        .Text = Format(Val(txtDiscPer), "#########.#0")
        'Discount amount
        .Col = 9
        .CellAlignment = 6
        .Text = Format(Val(txtDiscAmt), "#########.#0")
        '****************************
        'Discount OFF Invoice
        .Col = 10
        .CellAlignment = 6
        .Text = Format(Val(TxtOffInvDiscPer), "#########.#0")
        'Discount amount
        .Col = 11
        .CellAlignment = 6
        .Text = Format(Val(txtOffInvDiscAmt), "#########.#0")
        
        '****************************
        
        '
        'Included amount
        .Col = 12
        .CellAlignment = 6
        '.Text = Format(Val(TxtRate) * Val(TxtQty) + Val(TxtStaxAmount) - Val(txtDiscAmt) - Val(txtOffInvDiscAmt), "#########.#0")
        .Text = Format((((Val(TxtRate) * Val(TxtQty)) + Val(TxtStaxAmount)) - Val(txtDiscAmt)) - Val(txtOffInvDiscAmt), "#########.#0")
        
        ' Remarks
        .Col = 13
        .CellAlignment = 1
        .Text = TxtsRemarks
        
        ' Expiry Date
        .Col = 14
        .CellAlignment = 1
        .Text = Format(TxtExpDate.Value, "dd/MM/yyyy")
        
        
    End With
    mEditRowID = 0
    
    lEdit = False
    If lEdit = True Then
        Unload Me
        Exit Sub
    Else
        nCounter = nCounter + 1
    End If
   '******************************************************
   Call PUpdateBalance
   Call clearform
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub



Private Sub Form_Activate()
'On Error GoTo TrapError
'    txtBarcode.SetFocus
'Exit Sub
'TrapError:
'    Call ShowError(lngError, Me.Caption)
    
End Sub

Private Sub Form_KeyUp(Keycode As Integer, Shift As Integer)
'On Error GoTo TrapError
'    Call EnterKeyEnable(Keycode)
'Exit Sub
'TrapError:
'    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub Form_Paint()
On Error GoTo TrapError
    txtBarcode.SetFocus
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub LblItem_Click()
On Error GoTo TrapError
  'cSQLId = "ITEMID"
  cSelFormId = "Fin_PurD"
  Fin_Auto.Show vbModal, Me
  TxtID.SetFocus
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub



Private Sub Text1_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub Text1_Validate(Cancel As Boolean)
On Error GoTo TrapError
    Dim Rs As New ADODB.Recordset
    Dim cSQL As String
    If Val(Text1.Text) = 0 Or Len(Text1.Text) = 0 Then Exit Sub
    With Rs
'        .Open "select * from v_fin_item where manualid = " & CDbl(Text1), Con, adOpenKeyset, adLockPessimistic
        cSQL = "select * from v_fin_item where manualid = " & CDbl(Text1)
        Set Rs = FetchAll(cSQL)
        If Not (Rs.EOF And Rs.BOF) Then
            TxtID.Text = Rs!Item_ID
            txtUnit.Text = Rs!visacard_rate
            Call TxtID_Validate(False)
'            TxtOQty.SetFocus
        Else
            MsgBox "Manual ID not found."
        End If
        Rs.Close
    End With
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub




Private Sub txtBarcode_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub txtBarcode_Validate(Cancel As Boolean)
On Error GoTo TrapError
    Dim Rs As New ADODB.Recordset
    Dim cSQL As String
    If Val(txtBarcode.Text) = 0 Or Len(txtBarcode.Text) = 0 Then Exit Sub
    With Rs

'        cSQL = "select * from v_fin_item where barcodeid = '" & txtBarcode & "'"
        cSQL = "select * from v_fin_item where barcodeid = '" & txtBarcode & "'"
        Set Rs = FetchAll(cSQL)
        If Not (Rs.EOF And Rs.BOF) Then
            TxtID.Text = Rs!Item_ID
            txtUnit.Text = Rs!visacard_rate
            Call TxtID_Validate(False)
'            TxtOQty.SetFocus
        Else
            MsgBox "Barcode ID not found."
        End If
        Rs.Close
    End With
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub txtBarcodeWS_Validate(Cancel As Boolean)
On Error GoTo TrapError
    Dim Rs As New ADODB.Recordset
    Dim cSQL As String
    If Val(txtBarcodeWS.Text) = 0 Or Len(txtBarcodeWS.Text) = 0 Then Exit Sub
    With Rs

'        cSQL = "select * from v_fin_item where barcodeid = '" & txtBarcode & "'"
        cSQL = "select * from v_fin_item where barcodeid_ws = '" & txtBarcodeWS & "'"
        Set Rs = FetchAll(cSQL)
        If Not (Rs.EOF And Rs.BOF) Then
            TxtID.Text = Rs!Item_ID
            txtUnit.Text = Rs!visacard_rate
            Call TxtID_Validate(False)
            'WS rate
            lblSale.Caption = Rs!disc_p4
'            TxtOQty.SetFocus
        Else
            MsgBox "Barcode ID not found."
        End If
        Rs.Close
    End With
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub txtCoID_DblClick()
  cSQLId = "COID"
  cSelFormId = "COID_FIN_PUR"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub txtCoID_GotFocus()
'On Error GoTo TrapError
'    txtCoID.SelLength = Len(txtCoID)
'Exit Sub
'TrapError:
'    Call ShowError(lngError, Me.Caption)
End Sub


Private Sub txtCoID_KeyDown(Keycode As Integer, Shift As Integer)
    
    '
    If Keycode = 113 Then ' F2
        Call txtCoID_DblClick
    End If
    
    
End Sub

Private Sub txtCoID_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub txtCoID_Validate(Cancel As Boolean)
On Error GoTo TrapError
   If Val(txtCoID) = 0 Then
'        TxtID.SetFocus
        Exit Sub

   End If
   
   Screen.MousePointer = vbHourglass
   SQL = "SELECT * FROM co WHERE co_id = " & Val(txtCoID)
   Set Rs = FetchAll(SQL)
   If Not (Rs.EOF And Rs.BOF) Then
      lblCoTitle.Caption = "" & Rs!co_title
      
    Else
        Screen.MousePointer = vbNormal
        Rs.Close
        MsgBox "Company ID not found... ", vbInformation, "Purchase Receipt: Company ID"
        Cancel = True
        Exit Sub
    End If
    Rs.Close
    Screen.MousePointer = vbDefault
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub


Private Sub txtDiscAmt_GotFocus()
On Error GoTo TrapError
    txtDiscAmt.SelLength = Len(txtDiscAmt)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub txtDiscAmt_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub txtDiscAmt_Validate(Cancel As Boolean)
On Error GoTo TrapError
    If txtDiscAmt.Text = "" Then Exit Sub
    Call Calc_Rate
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub


Private Sub txtDiscPer_Change()
'    If Val(txtDiscPer) = 0 Then
'        txtDiscAmt.Enabled = True
'    Else
'        txtDiscAmt.Enabled = False
'    End If
'    If txtDiscPer.Text = "" Then Exit Sub
'    Call Calc_Rate
End Sub

Private Sub txtDiscPer_Validate(Cancel As Boolean)
On Error GoTo TrapError
'    If Val(txtDiscPer) = 0 Then
'        txtDiscAmt.Enabled = True
'    Else
'        txtDiscAmt.Enabled = False
'    End If
    If txtDiscPer.Text = "" Then Exit Sub
    Call Calc_Rate
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtID_DblClick()
On Error GoTo TrapError
  cSQLId = "Item Master"
  cSelFormId = "Fin_PurD"
  frmLookUp.Show vbModal, Me
  
  If Not TxtID.Text = "" Then
    TxtID_Validate (False)
  End If
  
  
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub


Private Sub CmdClear_Click()
On Error GoTo TrapError
    Call clearform
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub cmdClose_Click()
On Error GoTo TrapError
    Unload Me
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub
Private Sub Form_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
    Call EnterKeyEnable(KeyAscii)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub
Private Sub Form_KeyDown(Keycode As Integer, Shift As Integer)
On Error GoTo errhandler
    If Keycode = vbKeyF5 Then ' F3
        Dim X As Integer
        
        If MsgBox("Do you want to take a print :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
        
            If MsgBox("Do you want to hide price :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
                PrintPriceZero = True
            Else
                PrintPriceZero = False
            End If
                
                SQL = "select * from v_fin_item where item_id = " & TxtID.Text
                cSelcriteria = SQL
                'LstInvStore_short_PrnDesc.Show vbModal, Me
                'Exit Sub
                
                
'                txtNoOf = TxtQty.Text
                
'                For X = 1 To txtNoOf
                
                    With LstInvStore_short_PrnDesc
                           .ARC.Refresh
                           .Refresh
                            .ARC.Connection = Con
                            .ARC.Source = cSelcriteria
                '           .ARC.DatabaseName = cAppDb_ID
                '           .ARC.RecordSource = cSelcriteria
                '           .MCName = cName
                '           .Caption = cReportTitle
                '           .Printer.PaperSize = 6
                           .PageSettings.BottomMargin = 0 ' 1 inch bottom margin
                           .PageSettings.TopMargin = 0 ' 1 inch top margin
                           .PageSettings.LeftMargin = 0 '150 ' ? inch left margin
                           .PageSettings.RightMargin = 0 ' ? inch right margin
                            .PageSettings.PaperWidth = 2163 '72.1
                            .PageSettings.PaperHeight = 1617 '10276
                            '.PageSettings.PaperWidth = 72.1
                            '.PageSettings.PaperHeight = 10276
                           ' Printing Orientation Portrait/Landscape
                           ''iOrientationSav = Printer.Orientation
                           .Printer.Orientation = ddOPortrait
                           .Printer.Copies = Val(TxtQty.Text)
                           .PrintReport False
                    End With
                    Set LstInvStore_short_PrnDesc = Nothing
'                Next
        Else
            
            
                    
            If MsgBox("Do you want to hide price :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
                PrintPriceZero = True
            Else
                PrintPriceZero = False
            End If
            
            SQL = "select * from v_fin_item where item_id = " & TxtID.Text
            cSelcriteria = SQL
    
            With LstInvStore_short_PrnDesc
                .PageSettings.PaperWidth = 2163 '72.1
                .PageSettings.PaperHeight = 1617 '10276
            End With
            LstInvStore_short_PrnDesc.Show vbModal, Me
        
        End If
        
    End If
'
'    If KeyCode = 114 Then ' F3
'        Call LblItem_Click
'    End If
'    If KeyCode = 113 Then ' F2
'        Call TxtID_DblClick
'    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear
End Sub
Private Sub Form_Load(): Call FormDisplaySetting(Me)
On Error GoTo TrapError
    '
'    If Mid(Trim(cUPwordStr), 1, 1) = 0 Then
'        CmdItem.Enabled = False
'    End If
    
    TxtExpDate.Value = nDate
    
    If mID(Trim(cUPwordStr), 22, 1) = 0 Then
       CmdItem.Enabled = False
    End If
  
    
    Caption = cName
    TxtID.MaxLength = cFinSeg1 + cFinSeg2 + cFinSeg3 + cFinSeg4
'    cFoundFlag = False
   If lEdit = True Then
        With Fin_PurM_JSON.VGrid
            mEditRowID = .Row
            .Col = 1
            TxtID.Text = Trim(.Text)
            .Col = 2
            TxtTitle.Caption = "" & Trim(.Text)
            .Col = 3
            TxtQty.Text = .Text
            .Col = 4
            TxtRate.Text = .Text
            .Col = 5
            TxtAmount.Caption = .Text
            
            .Col = 6
            TxtStaxRate.Text = .Text
            .Col = 7
            TxtStaxAmount.Text = .Text
            
            .Col = 8
            txtDiscPer.Text = .Text
            .Col = 9
            txtDiscAmt.Text = .Text
            
            .Col = 10
            TxtOffInvDiscPer.Text = .Text
            
            .Col = 11
            txtOffInvDiscAmt.Text = .Text
            
            
            .Col = 12
            LblIncludedAmount = .Text
            .Col = 13
            TxtsRemarks.Text = .Text
            
            .Col = 14
'            TxtExpDate.Value = CDate(.Text)
            TxtExpDate.Value = Format(CDate(.Text), "dd/MM/yyyy")
            
            Call TxtID_Validate(False)
            Call txtDiscAmt_Validate(False)
            Call TxtStaxAmount_Validate(False)
            Call txtOffInvDiscAmt_Validate(False)
        End With
    Else
        mEditRowID = 0
   End If
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub
Private Function clearform()
On Error GoTo TrapError
   ' Clear Data Fields
   
    With grd(0)
        .Cols = 5
        .TextMatrix(0, 0) = "Pur.#"
        .ColWidth(0) = 1100
        .TextMatrix(0, 1) = "Date"
        .ColWidth(1) = 1300
        .TextMatrix(0, 2) = "Qty"
        .ColWidth(2) = 1100
        .TextMatrix(0, 3) = "Rate"
        .ColWidth(3) = 1100
        .TextMatrix(0, 4) = "Item ID"
        .ColWidth(4) = 1500
        .Clear
    End With
   TxtID.Text = ""
   TxtTitle.Caption = ""
   LblMainTitle.Caption = ""
   LblSubTitle.Caption = ""
   TxtQty.Text = "0"
   TxtRate.Text = "0"
   txtNetCost.Text = "0"
   txtMRP.Text = "0"
   TxtStaxRate = "0"
   txtDiscPer.Text = ""
   txtDiscAmt.Text = "0"
   TxtAmount.Caption = ""
   TxtStaxAmount.Text = ""
   LblIncludedAmount.Caption = ""
   TxtUomTitle.Caption = ""
   TxtsRemarks.Text = ""
   Text1.Text = ""
   txtUnit.Text = ""
   txtPQty.Text = ""
   TxtPRate.Text = ""
   txtBarcode.Text = ""
   txtBarcodeWS.Text = ""
'   TxtID.SetFocus
   txtBarcode.SetFocus
   lblProfitPer.Caption = "%"
   lblExcludAmt = "0"
   TxtOffInvDiscPer = "0"
   LblOffInvIncludedAmt = "0"
   txtOffInvDiscAmt = "0"
   txtCoID = "0"
   lblCoTitle.Caption = ""
   
Exit Function
TrapError:
    Call ShowError(lngError, Me.Caption)
End Function
Private Sub TxtItemID_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
    If KeyAscii = 27 Then
           Unload Me
    End If
    KeyAscii = CheckNumOrChr(KeyAscii, True, False)
''        Dim strvalid As String
''        strvalid = "0123456789"
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtID))
''            If mLen = 0 Then
''                TxtID.Text = ""
''            Else
''                TxtID.Text = Left(Trim(TxtID), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub Txtid_GotFocus()
On Error GoTo TrapError
    TxtID.SelLength = Len(TxtID)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtID_KeyDown(Keycode As Integer, Shift As Integer)
'
    If Keycode = 113 Then ' F2
        Call TxtID_DblClick
    End If
End Sub

Private Sub TxtID_Validate(Cancel As Boolean)
On Error GoTo TrapError
Dim Rs As New ADODB.Recordset

   If Len(Trim(TxtID)) = 0 Then
        Exit Sub
   End If
   If Len(Trim(TxtID)) < 10 Then
'   cSeg1 + cSeg2 + cSeg3 + cSeg4 Then
        MsgBox "Invalid ID length ", vbInformation, cSelFormId
        TxtID.SetFocus
        Cancel = True
        Exit Sub
   End If
      Screen.MousePointer = vbHourglass
        SQL = "select * from FIN_ITEM where item_id=" & Val(TxtID)
        Set RsDummy = FetchAll(SQL)
        If Not (RsDummy.EOF And RsDummy.BOF) Then
            Text1.Text = RsDummy!manualid
            'TxtTitle.Caption = RsDummy!Item_Title & " --- " & RsDummy!item_short
            TxtTitle.Caption = RsDummy!Item_Title & " --- " & RsDummy!manualid
            txtCoID.Text = RsDummy!co_id
            txtCoID_Validate (False)
            '
            If RsDummy!sales_Rate > 0 Then
                lblSale.Caption = Format(RsDummy!sales_Rate, "########.00")
            Else
                lblSale.Caption = "0.00"
            End If
            
            If RsDummy!Cqty > 0 Then
                lblStock.Caption = RsDummy!Cqty
            Else
                lblStock.Caption = "0.00"
            End If
            
            If RsDummy!disc_p1 > 0 Then
                txtMRP.Text = RsDummy!disc_p1
            Else
                txtMRP.Text = "0"
            End If
            
            If RsDummy!Cqty1 > 0 Then
                TxtRate.Text = Format(RsDummy!Cqty1, "########.#000")
            Else
'                TxtRate.Text = "0"
            End If
            
            If RsDummy!STAX_REG > 0 Then
                TxtStaxRate.Text = RsDummy!STAX_REG
            Else
                TxtStaxRate.Text = "0"
            End If
            
            
            
            
            If lEdit = False Then
                If RsDummy!cost_Rate > 0 Then
                    'Temporary Close
                    'TxtRate.Text = Format(RsDummy!cost_Rate, "########.00")
                Else
                    'TxtRate.Text = ""
                End If
                
                
            End If
            mUomID = RsDummy!uom_id
            SQL = "SELECT * FROM fin_c002 WHERE uom_id = " & mUomID
            Set Rs = FetchAll(SQL)
            If Not (Rs.EOF And Rs.BOF) Then
              ' Assign Values to Text/Controls
              TxtUomTitle.Caption = "" & Rs!uom_abbr
            Else
                 TxtUomTitle.Caption = "UOM ID not found ...... "
            End If
            Rs.Close
            
            If RsDummy!ed_status = 1 Then
                Screen.MousePointer = vbDefault
                MsgBox "Item ID is Disabled, Consultant Administrator .... ", vbInformation, cSelFormId
                Cancel = True
                Exit Sub
            End If
            If lEdit = False Then
                If RsDummy!cost_Rate > 0 Then
'                    TxtRate.Text = Format(RsDummy!cost_Rate, "########.00")  'RsDummy!cost_Rate
                Else
                    TxtRate.Text = ""
                End If
            End If
            ' *************************************************
            If cSTaxType = 0 Then
               If Fin_PurM_JSON.LblRegistration.Caption = "Registered" Then
                If lEdit = False Then
'                   mSaleTaxRate = RsDummy!STAX_REG
'                   TxtStaxRate = mSaleTaxRate
                End If
    
               Else
               If lEdit = False Then
'                   mSaleTaxRate = RsDummy!STAX_UNREG
'                   TxtStaxRate = mSaleTaxRate
               End If
               End If
            Else
               ' For fix Sales Tax Rate (not dependent on item)
            If lEdit = False Then
'               TxtStaxRate = cSalesTaxRate
'               mSaleTaxRate = cSalesTaxRate
            End If
            End If
            ' *************************************************
'            If Not IsNull(RsDummy!ed_status) Then
'                If RsDummy!ed_status Then
'                   MsgBox "Account ID is Diabled, please re-enter another ... ", vbCritical, cSelFormId
'                   TxtID.Text = ""
'                   TxtID.SetFocus
'                   Cancel = True
'                   Exit Sub
'                End If
'            End If
        Else
            Screen.MousePointer = vbDefault
            MsgBox "Item ID not found, please re-enter ... " & Chr(13) & Chr(13) & " Or Main Or Sub Account ID is selected. ", vbInformation, "Production Receipt"
            TxtID.SetFocus
            Cancel = True
            Exit Sub
        End If
        Set RsDummy = Nothing 'KAM 06032022
        
        SQL = "select * from v_FIN_ITEM where item_id=" & CDbl(TxtID)
        Set RsTmp = FetchAll(SQL)
        If Not (RsTmp.EOF And RsTmp.BOF) Then
             LblMainTitle.Caption = RsTmp!main_title
             LblSubTitle.Caption = RsTmp!sub_title
        Else
             LblMainTitle.Caption = "Not found . "
             LblSubTitle.Caption = "Not found. "
        End If
        RsTmp.Close
        
                'SQL = "select * from FIN_ITEM where item_id=" & Val(TxtID)
                'SQL = "select top " & txtNoOf.Text & " Prod_id,doc_date,QTY,((pur_AMT - disc_amt - disc_amt_oi )/QTY) as cost_amt ,rate as TP,item_id from Fin_Pur_D " & _

                SQL = "select top " & txtNoOf.Text & " Prod_id,doc_date,QTY,rate as TP,item_id from Fin_Pur_D " & _
                        "where ITEM_ID = '" & TxtID.Text & "' " & _
                            "order by doc_date desc"
                Set Rs = FetchAll(SQL)
                If Not (Rs.EOF And Rs.BOF) Then
                    grd(0).LoadArray Rs.GetRows()
                End If
                With grd(0)
                    .Cols = 5
                    .TextMatrix(0, 0) = "Pur.#"
                    .ColWidth(0) = 1100
                    .TextMatrix(0, 1) = "Date"
                    .ColWidth(1) = 1300
                    .TextMatrix(0, 2) = "Qty"
                    .ColWidth(2) = 1100
                    .TextMatrix(0, 3) = "TP Rate"
                    .ColWidth(3) = 1100
                    .TextMatrix(0, 4) = "ITEM ID"
                    .ColWidth(4) = 1500
                End With
                Set Rs = Nothing 'KAM 06032022
        
        Screen.MousePointer = vbDefault
        
        Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub txtOffInvDiscAmt_GotFocus()
On Error GoTo TrapError
    txtOffInvDiscAmt.SelLength = Len(txtOffInvDiscAmt)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub txtOffInvDiscAmt_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub txtOffInvDiscAmt_Validate(Cancel As Boolean)
On Error GoTo TrapError
    If txtOffInvDiscAmt.Text = "" Then Exit Sub
    Call Calc_Rate
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub



'Private Sub txtOffInvDiscAmt_Change()
'On Error GoTo TrapError
'    If txtOffInvDiscAmt.Text = "" Then Exit Sub
'    Call Calc_Rate
'Exit Sub
'TrapError:
'    Call ShowError(lngError, Me.Caption)
'End Sub

Private Sub TxtPQty_Change()
On Error GoTo TrapError
    If (txtPQty.Text) = "" Or (txtUnit.Text) = "" Then Exit Sub
    TxtQty.Text = CDbl(txtUnit.Text) * CDbl(txtPQty.Text)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtPQty_GotFocus()
On Error GoTo TrapError
    If txtUnit.Text = "0" Or txtUnit.Text = "" Then
        TxtQty.SetFocus
        Exit Sub
    End If
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub


Private Sub txtPQty_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub TxtPRate_Change()
On Error GoTo TrapError
    If (txtUnit.Text) = "" Or (TxtPRate.Text) = "" Then Exit Sub
    TxtRate.Text = Format(CDbl(TxtPRate.Text) / CDbl(txtUnit.Text), "#########.#000")
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtPRate_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub


Private Sub TxtPRate_LostFocus()
On Error GoTo TrapError
    TxtStaxRate.SetFocus
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub


Private Sub TxtQty_GotFocus()
On Error GoTo TrapError
    TxtQty.SelLength = Len(TxtQty)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub TxtQty_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub


Private Sub TxtQty_Validate(Cancel As Boolean)
On Error GoTo TrapError
    TxtAmount.Caption = Format(Val(TxtRate) * Val(TxtQty), "#########.#0")
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtRate_Change()
On Error GoTo TrapError
    If Val(TxtRate.Text) <> 0 Then
        If lblSale.Caption <> 0 Then
            Dim RateDiff As Integer
            RateDiff = Val(lblSale.Caption) - Val(TxtRate.Text)
            'lblProfitPer.Caption = Format((100 - ((Val(txtrate.text) / Val(lblsale.caption)) * 100)), "########.#0")
            'lblProfitPer.Caption = CDbl(Format(((RateDiff * 100) / (Val(txtrate.text))), "########.#0"))
            lblProfitPer.Caption = CDbl(Format(((RateDiff / Val(TxtRate.Text) * 100)), "########.#0"))
        End If
    End If
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtRate_GotFocus()
On Error GoTo TrapError
    TxtRate.SelLength = Len(TxtRate)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub TxtRate_KeyDown(Keycode As Integer, Shift As Integer)
On Error GoTo errhandler
Dim Rs As New ADODB.Recordset
    If Keycode = 113 Then ' F2
        Screen.MousePointer = vbHourglass
            If Me.Height <= 4560 Then
                Me.Height = 8250 '11955
                Me.Left = (Screen.Width - Me.Width) / 2
                Me.Top = (Screen.Height - Me.Height) / 2
            Else
                Me.Height = 4560
                Me.Left = (Screen.Width - Me.Width) / 2
                Me.Top = (Screen.Height - Me.Height) / 2
                
            End If
    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear

End Sub

Private Sub TxtRate_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError



If KeyAscii = 27 Then
               Unload Me
        End If
    KeyAscii = CheckNumOrChr(KeyAscii, True, True)
''        Dim strvalid As String
''        strvalid = "0123456789."
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtRate))
''            If mLen = 0 Then
''                TxtRate.Text = ""
''            Else
''                TxtRate.Text = Left(Trim(TxtRate), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub
Private Sub TxtRate_LostFocus()
On Error GoTo TrapError

'Temp rate block
'    If Val(TxtRate) = 0 And cAudit = 0 Then
'        MsgBox "Invalid:  Please enter Rate ...  ", vbInformation, "Production Receipt"
'        Exit Sub
'    End If

'    If TxtRate.Text <> 0 Then
'        If lblSale.Caption <> 0 Then
'            Dim RateDiff As Integer
'            RateDiff = Val(lblSale.Caption) - Val(TxtRate.Text)
'            'lblProfitPer.Caption = Format((100 - ((Val(txtrate.text) / Val(lblsale.caption)) * 100)), "########.#0")
'            'lblProfitPer.Caption = CDbl(Format(((RateDiff * 100) / (Val(txtrate.text))), "########.#0"))
'            lblProfitPer.Caption = CDbl(Format(((RateDiff / Val(TxtRate.Text) * 100)), "########.#0"))
'        End If
'    End If
    

    If Val(TxtQty) = 0 Then
        MsgBox "Invalid:  Please enter Quantity ...  ", vbInformation, "Production Receipt"
        Exit Sub
    End If
    TxtAmount.Caption = Format(Val(TxtRate) * Val(TxtQty), "#########.#0")
    
    Call Calc_Rate
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtStaxAmount_GotFocus()
On Error GoTo TrapError
    TxtStaxAmount.SelLength = Len(TxtStaxAmount)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtStaxAmount_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub TxtStaxAmount_Validate(Cancel As Boolean)
On Error GoTo TrapError
    Call Calc_Rate
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtStaxRate_GotFocus()
On Error GoTo TrapError
    TxtStaxRate.SelLength = Len(TxtStaxRate)
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

Private Sub TxtStaxRate_KeyPress(KeyAscii As Integer)
On Error GoTo TrapError
        If KeyAscii = 27 Then
               Unload Me
        End If
        KeyAscii = CheckNumOrChr(KeyAscii, True, True)

Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)

End Sub

Private Sub TxtStaxRate_Validate(Cancel As Boolean)
On Error GoTo TrapError
'    If Val(TxtStaxRate) = 0 Then
'        TxtStaxAmount.Enabled = True
'    Else
'        TxtStaxAmount.Enabled = False
'    End If
'    Call Calc_Rate
Exit Sub
TrapError:
    Call ShowError(lngError, Me.Caption)
End Sub

'*********************************************************************
' Import From Excel  (fin_pur_d)
' Folder: \\shaheenhp\Backup\Purchase Format
' Filename must START WITH Supplier ID from Fin_PurM_JSON.TxtID
' Reads ONLY Worksheets(2)
' A=Text1(Manual ID)  B=TxtQty  C=TxtRate  D=TxtStaxRate
' E=txtDiscAmt  F=TxtStaxAmount
' Blank Manual ID = STOP. Qty=0 = SKIP. Uses existing CmdSave_Click.
'*********************************************************************
Private Sub cmdImportExcel_Click()
On Error GoTo TrapError
    Dim sSupplierID As String
    Dim sFOlder As String
    Dim sFile As String
    Dim sFullPath As String
    Dim xlApp As Excel.Application
    Dim xlWB As Excel.Workbook
    Dim xlWs As Excel.Worksheet
    Dim nRow As Long
    Dim sManualID As String
    Dim sQtyRaw As String
    Dim sRateRaw As String
    Dim sStaxRateRaw As String
    Dim sDiscAmtRaw As String
    Dim sStaxAmtRaw As String
    Dim dQty As Double
    Dim nBefore As Integer
    Dim nImported As Integer
    Dim nSkippedQty As Integer
    Dim nErrors As Integer
    Dim nProcessed As Integer
    Dim sLog As String
    Dim sErr As String
    Dim bDup As Boolean
    Dim iCounter As Integer
    Dim cSQL As String
    Dim RsChk As ADODB.Recordset
    Dim Cancel As Boolean

    ' 1) Supplier/Customer ID from Purchase Master
    sSupplierID = Trim(Fin_PurM_JSON.TxtID.Text)
    If Len(sSupplierID) = 0 Or Val(sSupplierID) = 0 Then
        MsgBox "Please select Supplier/Customer before importing Excel data.", vbInformation, cSelFormId
        Exit Sub
    End If

    ' 2) Import folder (network share; optional override via ImportPath.ini)
    sFOlder = ImportExcel_GetFolder()
    On Error Resume Next
    Err.Clear
    sFile = Dir(sFOlder & "\*.*")
    If Err.Number <> 0 Then
        On Error GoTo TrapError
        MsgBox "Import folder not found / not accessible:" & vbCrLf & sFOlder & vbCrLf & _
               Err.Description, vbExclamation, cSelFormId
        Exit Sub
    End If
    On Error GoTo TrapError
    sFile = ""

    ' 3) Find SupplierID*.xlsx (and .xls) ? match at START of filename only
    sFile = ImportExcel_SelectFile(sFOlder, sSupplierID)
    If Len(sFile) = 0 Then Exit Sub
    sFullPath = sFOlder & "\" & sFile
    If Len(Dir(sFullPath)) = 0 Then
        MsgBox "Excel file not found:" & vbCrLf & sFullPath, vbExclamation, cSelFormId
        Exit Sub
    End If

    Screen.MousePointer = vbHourglass
    Set xlApp = New Excel.Application
    xlApp.Visible = False
    xlApp.DisplayAlerts = False
    Set xlWB = xlApp.Workbooks.Open(sFullPath, ReadOnly:=True)
    If xlWB.Worksheets.count < 2 Then
        MsgBox "Workbook has no Sheet 2:" & vbCrLf & sFullPath, vbExclamation, cSelFormId
        GoTo CleanUp
    End If
    Set xlWs = xlWB.Worksheets(2)   ' index 2 only - do not use sheet name

    nRow = 1
    nImported = 0
    nSkippedQty = 0
    nErrors = 0
    nProcessed = 0
    sLog = ""
    lEdit = False

    Do
        Me.Caption = "Importing Excel row " & nRow & " ..."
        DoEvents

        ' --- Manual ID (Column A = Text1) ? STOP when blank ---
        sManualID = Trim$(ImportExcel_CellText(xlWs.Cells(nRow, 1).Value))
        If Len(sManualID) = 0 Then
            sLog = sLog & "Row " & nRow & ": STOPPED_MANUAL_ID_BLANK" & vbCrLf
            Exit Do
        End If

        nProcessed = nProcessed + 1

        ' Qty (Column B)
        sQtyRaw = Trim$(ImportExcel_CellText(xlWs.Cells(nRow, 2).Value))
        If Not ImportExcel_IsNumber(sQtyRaw) Then
            nErrors = nErrors + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & _
                   ": ERROR Invalid Qty value """ & sQtyRaw & """" & vbCrLf
            nRow = nRow + 1
            GoTo ContinueRow
        End If
        dQty = CDbl(sQtyRaw)

        ' Qty = 0 ? SKIP (do not save)
        If dQty = 0 Then
            nSkippedQty = nSkippedQty + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & ": SKIPPED_QTY_ZERO" & vbCrLf
            nRow = nRow + 1
            GoTo ContinueRow
        End If

        ' Remaining columns
        sRateRaw = Trim$(ImportExcel_CellText(xlWs.Cells(nRow, 3).Value))
        sStaxRateRaw = Trim$(ImportExcel_CellText(xlWs.Cells(nRow, 4).Value))
        sDiscAmtRaw = Trim$(ImportExcel_CellText(xlWs.Cells(nRow, 5).Value))
        sStaxAmtRaw = Trim$(ImportExcel_CellText(xlWs.Cells(nRow, 6).Value))

        sErr = ""
        If Len(sRateRaw) > 0 And Not ImportExcel_IsNumber(sRateRaw) Then sErr = "Invalid Rate value """ & sRateRaw & """"
        If Len(sErr) = 0 And Len(sStaxRateRaw) > 0 And Not ImportExcel_IsNumber(sStaxRateRaw) Then sErr = "Invalid StaxRate value """ & sStaxRateRaw & """"
        If Len(sErr) = 0 And Len(sDiscAmtRaw) > 0 And Not ImportExcel_IsNumber(sDiscAmtRaw) Then sErr = "Invalid DiscAmt value """ & sDiscAmtRaw & """"
        If Len(sErr) = 0 And Len(sStaxAmtRaw) > 0 And Not ImportExcel_IsNumber(sStaxAmtRaw) Then sErr = "Invalid StaxAmount value """ & sStaxAmtRaw & """"
        If Len(sErr) > 0 Then
            nErrors = nErrors + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & ": ERROR " & sErr & vbCrLf
            nRow = nRow + 1
            GoTo ContinueRow
        End If

        ' Manual ID must exist (avoid Text1_Validate MsgBox spam)
        If Not IsNumeric(sManualID) Then
            nErrors = nErrors + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & ": ERROR Manual ID is not numeric." & vbCrLf
            nRow = nRow + 1
            GoTo ContinueRow
        End If
        cSQL = "select item_id from v_fin_item where manualid = " & CDbl(sManualID)
        Set RsChk = FetchAll(cSQL)
        If RsChk.EOF And RsChk.BOF Then
            RsChk.Close
            nErrors = nErrors + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & ": ERROR Manual ID not found." & vbCrLf
            nRow = nRow + 1
            GoTo ContinueRow
        End If
        RsChk.Close

        ' Transaction limit
        If nCounter > max_entries Then
            nErrors = nErrors + 1
            sLog = sLog & "Row " & nRow & ": ERROR Limit of Transactions exhausted." & vbCrLf
            Exit Do
        End If

        ' Populate existing controls (same order as manual entry)
        Call clearform
        Text1.Text = sManualID
        Cancel = False
        Call Text1_Validate(Cancel)   ' loads Item ID / Co ID via existing logic
        If Val(TxtID.Text) = 0 Then
            nErrors = nErrors + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & ": ERROR Item not loaded." & vbCrLf
            nRow = nRow + 1
            GoTo ContinueRow
        End If

        ' Duplicate protection (same check as CmdSave_Click)
        bDup = False
        With Fin_PurM_JSON.VGrid
            iCounter = 0
            Do While iCounter + 1 <> .Rows
                .Row = iCounter + 1
                .Col = 1
                If Val(.Text) = Val(TxtID.Text) Then
                    bDup = True
                    Exit Do
                End If
                iCounter = iCounter + 1
            Loop
        End With
        If bDup Then
            nErrors = nErrors + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & _
                   ": ERROR Duplicate: Item ID Already Exists .... " & vbCrLf
            nRow = nRow + 1
            GoTo ContinueRow
        End If

        ' Excel values AFTER item load (override item defaults)
        TxtQty.Text = sQtyRaw
        If Len(sRateRaw) > 0 Then TxtRate.Text = sRateRaw
        If Len(sStaxRateRaw) > 0 Then TxtStaxRate.Text = sStaxRateRaw
        If Len(sDiscAmtRaw) > 0 Then txtDiscAmt.Text = sDiscAmtRaw
        If Len(sStaxAmtRaw) > 0 Then TxtStaxAmount.Text = sStaxAmtRaw

        Call Calc_Rate

        ' Existing Save ? must succeed (nCounter advances on success)
        nBefore = nCounter
        Call CmdSave_Click
        If nCounter > nBefore Then
            nImported = nImported + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & ": IMPORTED" & vbCrLf
        Else
            nErrors = nErrors + 1
            sLog = sLog & "Row " & nRow & " ManualID " & sManualID & ": ERROR Save did not complete." & vbCrLf
        End If

        nRow = nRow + 1
ContinueRow:
    Loop

CleanUp:
    On Error Resume Next
    If Not xlWB Is Nothing Then xlWB.Close SaveChanges:=False
    If Not xlApp Is Nothing Then
        xlApp.Quit
    End If
    Set xlWs = Nothing
    Set xlWB = Nothing
    Set xlApp = Nothing
    On Error GoTo TrapError

    Screen.MousePointer = vbDefault
    Me.Caption = "Abc Company"
    Call clearform

    MsgBox "Excel Import Completed" & vbCrLf & vbCrLf & _
           "File: " & sFile & vbCrLf & _
           "Imported: " & nImported & vbCrLf & _
           "Skipped Qty = 0: " & nSkippedQty & vbCrLf & _
           "Errors: " & nErrors & vbCrLf & _
           "Total Processed: " & nProcessed & vbCrLf & vbCrLf & _
           Left$(sLog, 1500), vbInformation, cSelFormId
Exit Sub
TrapError:
    Screen.MousePointer = vbDefault
    On Error Resume Next
    If Not xlWB Is Nothing Then xlWB.Close SaveChanges:=False
    If Not xlApp Is Nothing Then xlApp.Quit
    Set xlWs = Nothing
    Set xlWB = Nothing
    Set xlApp = Nothing
    Me.Caption = "Abc Company"
    Call ShowError(lngError, Me.Caption)
End Sub

' Default: \\shaheenhp\Backup\Purchase Format
' Override: one-line path in App.Path\ImportPath.ini
Private Function ImportExcel_GetFolder() As String
On Error GoTo TrapError
    Dim sIni As String
    Dim sLine As String
    Dim nFile As Integer

    sIni = App.Path & "\ImportPath.ini"
    If Len(Dir(sIni)) > 0 Then
        nFile = FreeFile
        Open sIni For Input As #nFile
        If Not EOF(nFile) Then Line Input #nFile, sLine
        Close #nFile
        sLine = Trim$(sLine)
        If Len(sLine) > 0 Then
            If Right$(sLine, 1) = "\" Then sLine = Left$(sLine, Len(sLine) - 1)
            ImportExcel_GetFolder = sLine
            Exit Function
        End If
    End If

    ImportExcel_GetFolder = "\\shaheenhp\Backup\Purchase Format"
Exit Function
TrapError:
    ImportExcel_GetFolder = "\\shaheenhp\Backup\Purchase Format"
End Function

' Files whose name STARTS WITH supplier ID. Multiple ? user picks.
Private Function ImportExcel_SelectFile(ByVal sFOlder As String, ByVal sSupplierID As String) As String
On Error GoTo TrapError
    Dim Col As New Collection
    Dim sPat As String
    Dim sF As String
    Dim i As Integer
    Dim sList As String
    Dim sPick As String
    Dim nPick As Integer
    Dim sID As String

    sID = CStr(Val(sSupplierID))
    If Len(sID) = 0 Then Exit Function

    ' .xlsx then .xls
    sPat = sID & "*.xlsx"
    sF = Dir(sFOlder & "\" & sPat)
    Do While Len(sF) > 0
        ' Extra guard: must start with supplier ID (Dir already does this)
        If Left$(UCase$(sF), Len(sID)) = UCase$(sID) Then
            Col.Add sF
        End If
        sF = Dir
    Loop
    sPat = sID & "*.xls"
    sF = Dir(sFOlder & "\" & sPat)
    Do While Len(sF) > 0
        ' Skip .xlsx already collected (Dir *.xls can include .xlsx on some systems)
        If LCase$(Right$(sF, 4)) = ".xls" Then
            If Left$(UCase$(sF), Len(sID)) = UCase$(sID) Then
                Col.Add sF
            End If
        End If
        sF = Dir
    Loop

    If Col.count = 0 Then
        MsgBox "Excel file not found for Customer/Supplier ID: " & sID & _
               vbCrLf & "Folder: " & sFOlder, vbExclamation, cSelFormId
        Exit Function
    End If

    If Col.count = 1 Then
        ImportExcel_SelectFile = Col(1)
        Exit Function
    End If

    sList = "Customer/Supplier ID: " & sID & vbCrLf & vbCrLf & "Matching files:" & vbCrLf
    For i = 1 To Col.count
        sList = sList & i & ") " & Col(i) & vbCrLf
    Next
    sPick = InputBox(sList & vbCrLf & "Enter file number:", "Select Excel file", "1")
    If Len(Trim$(sPick)) = 0 Then Exit Function
    If Not IsNumeric(sPick) Then
        MsgBox "Invalid selection.", vbExclamation, cSelFormId
        Exit Function
    End If
    nPick = CInt(sPick)
    If nPick < 1 Or nPick > Col.count Then
        MsgBox "Invalid selection.", vbExclamation, cSelFormId
        Exit Function
    End If
    ImportExcel_SelectFile = Col(nPick)
Exit Function
TrapError:
    Call ShowError(lngError, Me.Caption)
End Function

Private Function ImportExcel_CellText(ByVal v As Variant) As String
On Error Resume Next
    If IsNull(v) Then
        ImportExcel_CellText = ""
    ElseIf IsEmpty(v) Then
        ImportExcel_CellText = ""
    Else
        ImportExcel_CellText = CStr(v)
    End If
End Function

Private Function ImportExcel_IsNumber(ByVal s As String) As Boolean
    Dim t As String
    t = Trim$(s)
    If Len(t) = 0 Then
        ImportExcel_IsNumber = False
        Exit Function
    End If
    ' Allow leading +/- and one decimal point
    ImportExcel_IsNumber = IsNumeric(t)
End Function

'*********************************************************************
' Edit in Excel  (fin_purd ? Excel)
' Same folder/file rules as Import (Fin_PurM_JSON.TxtID + ImportExcel_GetFolder)
' Sheet 1 only. Find Manual ID in Column A (= Text1).
' Update ONLY Column C = TxtQty, Column D = TxtRate. Save same workbook.
' Prefer the already-open Excel window; do not close/reopen after update.
' Does NOT change Import From Excel behavior.
'*********************************************************************
Private Sub cmdEditInExcel_Click()
On Error GoTo TrapError
    Dim sSupplierID As String
    Dim sManualID As String
    Dim sQty As String
    Dim sRate As String
    Dim sFolder As String
    Dim sFile As String
    Dim sFullPath As String
    Dim xlApp As Excel.Application
    Dim xlWb As Excel.Workbook
    Dim xlWs As Excel.Worksheet
    Dim nLastRow As Long
    Dim nRow As Long
    Dim nMatchCount As Integer
    Dim nMatchRow As Long
    Dim sMatchRows As String
    Dim sCell As String
    Dim bSaved As Boolean
    Dim bWeStartedExcel As Boolean

    ' --- validation ---
    sSupplierID = Trim$(Fin_PurM_JSON.TxtID.Text)
    If Len(sSupplierID) = 0 Or Val(sSupplierID) = 0 Then
        MsgBox "Please select/enter Supplier or Customer ID.", vbInformation, cSelFormId
        Exit Sub
    End If

    sManualID = Trim$(Text1.Text)
    If Len(sManualID) = 0 Then
        MsgBox "Please enter Manual ID.", vbInformation, cSelFormId
        Text1.SetFocus
        Exit Sub
    End If

    sQty = Trim$(TxtQty.Text)
    If Len(sQty) = 0 Or Not ImportExcel_IsNumber(sQty) Then
        MsgBox "Please enter a valid Quantity.", vbInformation, cSelFormId
        TxtQty.SetFocus
        Exit Sub
    End If

    sRate = Trim$(TxtRate.Text)
    If Len(sRate) = 0 Or Not ImportExcel_IsNumber(sRate) Then
        MsgBox "Please enter a valid Rate.", vbInformation, cSelFormId
        TxtRate.SetFocus
        Exit Sub
    End If

    ' --- find workbook using existing Excel folder + Supplier ID ---
    sFolder = ImportExcel_GetFolder()
    On Error Resume Next
    Err.Clear
    sFile = Dir(sFolder & "\*.*")
    If Err.Number <> 0 Then
        On Error GoTo TrapError
        MsgBox "Excel folder not found / not accessible:" & vbCrLf & sFolder, vbExclamation, cSelFormId
        Exit Sub
    End If
    On Error GoTo TrapError
    sFile = ""

    sFile = ImportExcel_SelectFile(sFolder, sSupplierID)
    If Len(sFile) = 0 Then Exit Sub
    sFullPath = sFolder & "\" & sFile

    Screen.MousePointer = vbHourglass
    bWeStartedExcel = False

    ' Prefer already-running Excel + already-open workbook (no reopen)
    Set xlApp = Nothing
    Set xlWb = Nothing
    On Error Resume Next
    Set xlApp = GetObject(, "Excel.Application")
    On Error GoTo TrapError

    If Not xlApp Is Nothing Then
        Set xlWb = EditExcel_FindOpenWorkbook(xlApp, sFullPath)
    End If

    If xlWb Is Nothing Then
        ' Workbook not open yet ? open once in visible Excel
        If xlApp Is Nothing Then
            Set xlApp = New Excel.Application
            bWeStartedExcel = True
        End If
        xlApp.Visible = True
        xlApp.ScreenUpdating = True
        xlApp.DisplayAlerts = False
        Set xlWb = xlApp.Workbooks.Open(sFullPath, ReadOnly:=False)
    End If

    If xlWb Is Nothing Then
        MsgBox "Unable to open Excel workbook:" & vbCrLf & sFullPath, vbExclamation, cSelFormId
        GoTo CleanUp
    End If
    If xlWb.Worksheets.Count < 1 Then
        MsgBox "Workbook has no worksheets:" & vbCrLf & sFullPath, vbExclamation, cSelFormId
        GoTo CleanUp
    End If
    Set xlWs = xlWb.Worksheets(1)   ' Sheet 1 only ? existing worksheet object

    ' --- search Column A for exact Manual ID ---
    nLastRow = xlWs.Cells(xlWs.Rows.Count, 1).End(xlUp).Row
    If nLastRow < 1 Then nLastRow = 1
    nMatchCount = 0
    nMatchRow = 0
    sMatchRows = ""

    For nRow = 1 To nLastRow
        sCell = Trim$(ImportExcel_CellText(xlWs.Cells(nRow, 1).Value))
        If EditExcel_ManualIdEqual(sCell, sManualID) Then
            nMatchCount = nMatchCount + 1
            If nMatchCount = 1 Then nMatchRow = nRow
            If Len(sMatchRows) > 0 Then sMatchRows = sMatchRows & ", "
            sMatchRows = sMatchRows & CStr(nRow)
        End If
    Next

    If nMatchCount = 0 Then
        MsgBox "Manual ID " & sManualID & " was not found in Excel Sheet 1.", vbExclamation, cSelFormId
        GoTo CleanUp
    End If

    If nMatchCount > 1 Then
        MsgBox "Multiple records found for Manual ID: " & sManualID & vbCrLf & vbCrLf & _
               "Excel rows: " & sMatchRows & vbCrLf & vbCrLf & _
               "No changes were made.", vbExclamation, cSelFormId
        GoTo CleanUp
    End If

    ' --- update ONLY C (Qty) and D (Rate) on the existing worksheet ---
    xlApp.ScreenUpdating = True
    xlWs.Activate
    xlWs.Cells(nMatchRow, 3).Value = CDbl(sQty)     ' Column C = TxtQty
    xlWs.Cells(nMatchRow, 4).Value = CDbl(sRate)    ' Column D = TxtRate

    ' Force Excel to process/display the change in the open window
    On Error Resume Next
    xlApp.Calculate
    xlWs.Calculate
    xlApp.ScreenUpdating = True
    xlApp.Visible = True
    xlWb.Activate
    xlWs.Activate
    xlWs.Cells(nMatchRow, 3).Select
    On Error GoTo TrapError
    DoEvents

    ' --- save same workbook (do not Save As / reload / close) ---
    bSaved = False
    On Error Resume Next
    Err.Clear
    xlWb.Save
    If Err.Number <> 0 Then
        On Error GoTo TrapError
        MsgBox "Unable to save Excel file. Please make sure the file is not read-only or open by another user." & _
               vbCrLf & vbCrLf & sFullPath & vbCrLf & Err.Description, vbCritical, cSelFormId
        GoTo CleanUp
    End If
    On Error GoTo TrapError
    bSaved = True

    ' Keep Excel visible with updated cells ? do not close/reopen workbook
    xlApp.Visible = True
    xlApp.ScreenUpdating = True

CleanUp:
    ' Release our references only ? do NOT Close workbook / Quit Excel
    Set xlWs = Nothing
    Set xlWb = Nothing
    Set xlApp = Nothing

    Screen.MousePointer = vbDefault

    If bSaved Then
        MsgBox "Excel record updated successfully." & vbCrLf & vbCrLf & _
               "Customer/Supplier ID: " & sSupplierID & vbCrLf & _
               "Manual ID: " & sManualID & vbCrLf & _
               "Excel Row: " & nMatchRow & vbCrLf & _
               "Quantity: " & sQty & vbCrLf & _
               "Rate: " & sRate, vbInformation, cSelFormId
    End If
    ' keep fin_purd open with current values ? do not clearform / unload
Exit Sub
TrapError:
    Screen.MousePointer = vbDefault
    ' On error: release refs only; do not Quit Excel the user may already have open
    Set xlWs = Nothing
    Set xlWb = Nothing
    Set xlApp = Nothing
    Call ShowError(lngError, Me.Caption)
End Sub

' Find workbook already open in Excel (match full path; no reopen)
Private Function EditExcel_FindOpenWorkbook(ByVal xlApp As Excel.Application, ByVal sFullPath As String) As Excel.Workbook
On Error Resume Next
    Dim wb As Excel.Workbook
    Dim sWant As String
    Dim sWantName As String
    Dim sHave As String

    sWant = LCase$(Trim$(sFullPath))
    sWantName = LCase$(Mid$(sFullPath, InStrRev(sFullPath, "\") + 1))

    For Each wb In xlApp.Workbooks
        sHave = LCase$(Trim$(wb.FullName))
        If sHave = sWant Then
            Set EditExcel_FindOpenWorkbook = wb
            Exit Function
        End If
    Next

    ' Fallback: same file name already open (path may differ UNC vs mapped drive)
    For Each wb In xlApp.Workbooks
        If LCase$(Trim$(wb.Name)) = sWantName Then
            Set EditExcel_FindOpenWorkbook = wb
            Exit Function
        End If
    Next

    Set EditExcel_FindOpenWorkbook = Nothing
End Function

' Exact Manual ID compare (trim; numeric 38303 = text "38303")
Private Function EditExcel_ManualIdEqual(ByVal sExcel As String, ByVal sForm As String) As Boolean
    Dim a As String, b As String
    a = Trim$(sExcel)
    b = Trim$(sForm)
    If Len(a) = 0 Or Len(b) = 0 Then Exit Function
    If a = b Then
        EditExcel_ManualIdEqual = True
        Exit Function
    End If
    If IsNumeric(a) And IsNumeric(b) Then
        If CDbl(a) = CDbl(b) Then EditExcel_ManualIdEqual = True
    End If
End Function
