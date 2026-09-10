VERSION 5.00
Object = "{C0A63B80-4B21-11D3-BD95-D426EF2C7949}#1.0#0"; "Vsflex7L.ocx"
Object = "{BDC217C8-ED16-11CD-956C-0000C04E4C0A}#1.1#0"; "TabCtl32.ocx"
Begin VB.Form Fin_Item 
   BackColor       =   &H00C0C0C0&
   BorderStyle     =   4  'Fixed ToolWindow
   Caption         =   "Abc Company"
   ClientHeight    =   9255
   ClientLeft      =   45
   ClientTop       =   285
   ClientWidth     =   7965
   ControlBox      =   0   'False
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form1"
   LockControls    =   -1  'True
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   9255
   ScaleWidth      =   7965
   ShowInTaskbar   =   0   'False
   StartUpPosition =   1  'CenterOwner
   Begin VB.TextBox txtSavedCost_price 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   1395
      MaxLength       =   12
      TabIndex        =   125
      Top             =   5085
      Width           =   1395
   End
   Begin VB.CheckBox chkFocusManBar 
      BackColor       =   &H8000000A&
      Caption         =   "Set Focus"
      ForeColor       =   &H000000C0&
      Height          =   270
      Left            =   3105
      TabIndex        =   124
      Top             =   1800
      Width           =   1080
   End
   Begin VB.TextBox txtTPRate 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   6690
      MaxLength       =   12
      TabIndex        =   122
      Top             =   4770
      Width           =   1125
   End
   Begin VB.Frame Frame1 
      Caption         =   "Store Stock Levels"
      Height          =   960
      Left            =   1395
      TabIndex        =   89
      Top             =   3465
      Width           =   5685
      Begin VB.CheckBox chkPromotion 
         BackColor       =   &H8000000A&
         Caption         =   "Promotion"
         ForeColor       =   &H000000C0&
         Height          =   270
         Left            =   3945
         TabIndex        =   129
         Top             =   607
         Width           =   1665
      End
      Begin VB.TextBox TxtMax_Level1 
         Alignment       =   1  'Right Justify
         Height          =   315
         Left            =   3945
         MaxLength       =   12
         TabIndex        =   93
         Top             =   225
         Width           =   1665
      End
      Begin VB.TextBox TxtMin_Level1 
         Alignment       =   1  'Right Justify
         Height          =   315
         Left            =   1020
         MaxLength       =   12
         TabIndex        =   92
         Top             =   225
         Width           =   1665
      End
      Begin VB.TextBox TxtCritical_Level1 
         Alignment       =   1  'Right Justify
         Height          =   315
         Left            =   3945
         MaxLength       =   12
         TabIndex        =   91
         Top             =   585
         Visible         =   0   'False
         Width           =   1665
      End
      Begin VB.TextBox TxtRO_Qty1 
         Alignment       =   1  'Right Justify
         Height          =   315
         Left            =   1020
         MaxLength       =   12
         TabIndex        =   90
         Top             =   585
         Width           =   1665
      End
      Begin VB.Label Label30 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "&Reorder :"
         Height          =   195
         Left            =   45
         TabIndex        =   97
         Top             =   645
         Width           =   945
      End
      Begin VB.Label Label31 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Critital Level :"
         Height          =   195
         Left            =   2955
         TabIndex        =   96
         Top             =   645
         Visible         =   0   'False
         Width           =   945
      End
      Begin VB.Label Label32 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Min. Level :"
         Height          =   195
         Left            =   45
         TabIndex        =   95
         Top             =   285
         Width           =   945
      End
      Begin VB.Label Label33 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Max. Level :"
         Height          =   195
         Left            =   2955
         TabIndex        =   94
         Top             =   285
         Width           =   945
      End
   End
   Begin VB.TextBox txtManualID 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   1395
      MaxLength       =   10
      TabIndex        =   87
      Top             =   1755
      Width           =   1665
   End
   Begin VB.TextBox TxtRO_Qty 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   1395
      MaxLength       =   12
      TabIndex        =   86
      Top             =   3135
      Width           =   1665
   End
   Begin VB.TextBox TxtMin_Level 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   1395
      MaxLength       =   12
      TabIndex        =   85
      Top             =   2775
      Width           =   1665
   End
   Begin VB.ComboBox CboNature 
      Height          =   315
      Left            =   1395
      TabIndex        =   84
      Top             =   2430
      Width           =   1665
   End
   Begin VB.TextBox TxtUOMID 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   1395
      MaxLength       =   4
      TabIndex        =   82
      Top             =   2100
      Width           =   1665
   End
   Begin VB.TextBox TxtShortName 
      Height          =   315
      Left            =   1395
      MaxLength       =   10
      TabIndex        =   80
      Top             =   1395
      Width           =   1665
   End
   Begin VB.TextBox TxtID 
      Height          =   315
      Left            =   1395
      TabIndex        =   106
      Top             =   1050
      Width           =   1665
   End
   Begin VB.TextBox TxtCost_Price 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   1395
      MaxLength       =   12
      TabIndex        =   77
      Top             =   4440
      Width           =   1395
   End
   Begin VB.TextBox TxtSalesPWoGST 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   4455
      MaxLength       =   12
      TabIndex        =   81
      Top             =   4770
      Width           =   1395
   End
   Begin VB.TextBox txtGST 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   6690
      MaxLength       =   12
      TabIndex        =   75
      Top             =   5085
      Width           =   1125
   End
   Begin VB.TextBox txtCostWOGST 
      Alignment       =   1  'Right Justify
      Enabled         =   0   'False
      Height          =   315
      Left            =   1395
      MaxLength       =   12
      TabIndex        =   78
      Top             =   4770
      Width           =   1395
   End
   Begin VB.TextBox TxtMarket_Price 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   4455
      MaxLength       =   12
      TabIndex        =   10
      Top             =   5085
      Width           =   1395
   End
   Begin VB.CommandButton CmdClose 
      Caption         =   "&Close"
      CausesValidation=   0   'False
      Height          =   375
      Left            =   6825
      TabIndex        =   25
      Top             =   8790
      Width           =   1125
   End
   Begin VB.CommandButton CmdSave 
      Caption         =   "&Save"
      Height          =   375
      Left            =   45
      TabIndex        =   19
      Top             =   8790
      Width           =   1125
   End
   Begin VB.CommandButton CmdClear 
      Caption         =   "Clea&r"
      CausesValidation=   0   'False
      Height          =   375
      Left            =   1185
      TabIndex        =   20
      Top             =   8790
      Width           =   1125
   End
   Begin VB.CommandButton CmdDelete 
      Caption         =   "&Delete"
      Height          =   375
      Left            =   2325
      TabIndex        =   21
      Top             =   8790
      Width           =   1125
   End
   Begin VB.TextBox TxtMax_Level 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   4455
      MaxLength       =   12
      TabIndex        =   5
      Top             =   2775
      Width           =   1665
   End
   Begin VB.TextBox TxtCritical_Level 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   4455
      MaxLength       =   12
      TabIndex        =   6
      Top             =   3135
      Width           =   1665
   End
   Begin VB.TextBox TxtSales_Price 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   4455
      MaxLength       =   12
      TabIndex        =   79
      Top             =   4440
      Width           =   1395
   End
   Begin VB.CommandButton CmdView 
      Caption         =   "&View ID"
      Height          =   375
      Left            =   4560
      TabIndex        =   23
      Top             =   8790
      Width           =   1125
   End
   Begin VB.CheckBox ChkEDStatus 
      BackColor       =   &H8000000A&
      Caption         =   "Item Disabled"
      ForeColor       =   &H000000C0&
      Height          =   270
      Left            =   6150
      TabIndex        =   7
      Top             =   3150
      Width           =   1665
   End
   Begin VB.CommandButton CmdCategory 
      Caption         =   "Cate&gory"
      Height          =   375
      Left            =   3450
      TabIndex        =   22
      Top             =   8790
      Width           =   1125
   End
   Begin VB.TextBox TxtRemarks 
      Alignment       =   1  'Right Justify
      Height          =   330
      Left            =   1395
      MaxLength       =   50
      TabIndex        =   12
      Top             =   5392
      Width           =   1395
   End
   Begin VB.TextBox TxtCountryID 
      Alignment       =   1  'Right Justify
      Height          =   330
      Left            =   4455
      MaxLength       =   3
      TabIndex        =   4
      Top             =   2422
      Width           =   720
   End
   Begin VB.TextBox TxtCo 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   1395
      MaxLength       =   3
      TabIndex        =   17
      Top             =   5745
      Width           =   720
   End
   Begin VB.CheckBox chkCommission 
      Caption         =   "Commission Allowed"
      ForeColor       =   &H000000C0&
      Height          =   270
      Left            =   8460
      TabIndex        =   26
      Top             =   4410
      Visible         =   0   'False
      Width           =   1770
   End
   Begin VB.TextBox txtVisaCardRate 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   4455
      MaxLength       =   20
      TabIndex        =   14
      Top             =   5400
      Width           =   1395
   End
   Begin VB.TextBox txtBarcodeID 
      Height          =   315
      Left            =   5175
      MaxLength       =   20
      TabIndex        =   2
      Text            =   "0"
      Top             =   1755
      Width           =   2625
   End
   Begin VB.TextBox TxtOEM 
      Height          =   315
      Left            =   5175
      MaxLength       =   20
      TabIndex        =   0
      Top             =   1395
      Width           =   2625
   End
   Begin VB.TextBox txtWSPrice 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   6690
      MaxLength       =   12
      TabIndex        =   83
      Top             =   4455
      Width           =   1125
   End
   Begin VB.TextBox txtWSBarcodeid 
      Height          =   315
      Left            =   5175
      MaxLength       =   20
      TabIndex        =   3
      Top             =   2115
      Width           =   2625
   End
   Begin VB.CommandButton CmdManual 
      Caption         =   "&Manual"
      Height          =   375
      Left            =   5685
      TabIndex        =   24
      Top             =   8790
      Width           =   1125
   End
   Begin VB.TextBox txtNoOf 
      Alignment       =   1  'Right Justify
      Height          =   315
      Left            =   6690
      MaxLength       =   12
      TabIndex        =   88
      Text            =   "5"
      Top             =   5400
      Width           =   1125
   End
   Begin TabDlg.SSTab SSTab1 
      Height          =   2640
      Left            =   45
      TabIndex        =   18
      Top             =   6120
      Width           =   7920
      _ExtentX        =   13970
      _ExtentY        =   4657
      _Version        =   393216
      Tabs            =   5
      Tab             =   3
      TabsPerRow      =   5
      TabHeight       =   520
      TabCaption(0)   =   "General Ledger"
      TabPicture(0)   =   "Fin_Item.frx":0000
      Tab(0).ControlEnabled=   0   'False
      Tab(0).Control(0)=   "TxtGLPurID"
      Tab(0).Control(0).Enabled=   0   'False
      Tab(0).Control(1)=   "TxtGLStaxID"
      Tab(0).Control(1).Enabled=   0   'False
      Tab(0).Control(2)=   "TxtGLDiscID"
      Tab(0).Control(2).Enabled=   0   'False
      Tab(0).Control(3)=   "TxtGLConsID"
      Tab(0).Control(3).Enabled=   0   'False
      Tab(0).Control(4)=   "TxtGLSalesID"
      Tab(0).Control(4).Enabled=   0   'False
      Tab(0).ControlCount=   5
      TabCaption(1)   =   "Balances/S.Tax"
      TabPicture(1)   =   "Fin_Item.frx":001C
      Tab(1).ControlEnabled=   0   'False
      Tab(1).Control(0)=   "Label19"
      Tab(1).Control(0).Enabled=   0   'False
      Tab(1).Control(1)=   "TxtAverageCost"
      Tab(1).Control(1).Enabled=   0   'False
      Tab(1).Control(2)=   "Label35"
      Tab(1).Control(2).Enabled=   0   'False
      Tab(1).Control(3)=   "lblLastPurPer"
      Tab(1).Control(3).Enabled=   0   'False
      Tab(1).Control(4)=   "Label22"
      Tab(1).Control(4).Enabled=   0   'False
      Tab(1).Control(5)=   "Label21"
      Tab(1).Control(5).Enabled=   0   'False
      Tab(1).Control(6)=   "TxtOValue"
      Tab(1).Control(6).Enabled=   0   'False
      Tab(1).Control(7)=   "TxtCValue"
      Tab(1).Control(7).Enabled=   0   'False
      Tab(1).Control(8)=   "TxtCQty"
      Tab(1).Control(8).Enabled=   0   'False
      Tab(1).Control(9)=   "TxtOQty"
      Tab(1).Control(9).Enabled=   0   'False
      Tab(1).Control(10)=   "Label18"
      Tab(1).Control(10).Enabled=   0   'False
      Tab(1).Control(11)=   "Label17"
      Tab(1).Control(11).Enabled=   0   'False
      Tab(1).Control(12)=   "Label16"
      Tab(1).Control(12).Enabled=   0   'False
      Tab(1).Control(13)=   "Label15"
      Tab(1).Control(13).Enabled=   0   'False
      Tab(1).Control(14)=   "CmdPrnDes"
      Tab(1).Control(14).Enabled=   0   'False
      Tab(1).Control(15)=   "TxtSTaxUnReg"
      Tab(1).Control(15).Enabled=   0   'False
      Tab(1).Control(16)=   "TxtSTaxReg"
      Tab(1).Control(16).Enabled=   0   'False
      Tab(1).Control(17)=   "cmdPrnLabel"
      Tab(1).Control(17).Enabled=   0   'False
      Tab(1).Control(18)=   "CmdPrnDesExp"
      Tab(1).Control(18).Enabled=   0   'False
      Tab(1).Control(19)=   "cmdPrintRail"
      Tab(1).Control(19).Enabled=   0   'False
      Tab(1).Control(20)=   "cmdRailCardSM"
      Tab(1).Control(20).Enabled=   0   'False
      Tab(1).Control(21)=   "chkBarPrint"
      Tab(1).Control(21).Enabled=   0   'False
      Tab(1).Control(22)=   "cmdOpening"
      Tab(1).Control(22).Enabled=   0   'False
      Tab(1).ControlCount=   23
      TabCaption(2)   =   "Store Balances"
      TabPicture(2)   =   "Fin_Item.frx":0038
      Tab(2).ControlEnabled=   0   'False
      Tab(2).ControlCount=   0
      TabCaption(3)   =   "Last Purchases"
      TabPicture(3)   =   "Fin_Item.frx":0054
      Tab(3).ControlEnabled=   -1  'True
      Tab(3).Control(0)=   "grd(0)"
      Tab(3).Control(0).Enabled=   0   'False
      Tab(3).ControlCount=   1
      TabCaption(4)   =   "Last Sales"
      TabPicture(4)   =   "Fin_Item.frx":0070
      Tab(4).ControlEnabled=   0   'False
      Tab(4).Control(0)=   "grd(1)"
      Tab(4).ControlCount=   1
      Begin VB.CommandButton cmdOpening 
         Caption         =   "Opening Bal"
         CausesValidation=   0   'False
         Enabled         =   0   'False
         Height          =   315
         Left            =   -69645
         TabIndex        =   128
         Top             =   360
         Width           =   1770
      End
      Begin VB.CheckBox chkBarPrint 
         BackColor       =   &H8000000A&
         Caption         =   "Prin&t"
         ForeColor       =   &H000000C0&
         Height          =   270
         Left            =   -72120
         TabIndex        =   127
         Top             =   2295
         Width           =   675
      End
      Begin VB.CommandButton cmdRailCardSM 
         Caption         =   "Pri&nt Rail SM"
         CausesValidation=   0   'False
         Height          =   270
         Left            =   -73830
         TabIndex        =   73
         Top             =   2295
         Width           =   1125
      End
      Begin VB.CommandButton cmdPrintRail 
         Caption         =   "Pri&nt Rail "
         CausesValidation=   0   'False
         Height          =   270
         Left            =   -75000
         TabIndex        =   72
         Top             =   2295
         Width           =   1125
      End
      Begin VB.CommandButton CmdPrnDesExp 
         Caption         =   "Pri&nt Des Exp"
         CausesValidation=   0   'False
         Height          =   270
         Left            =   -70815
         TabIndex        =   71
         Top             =   2295
         Width           =   1125
      End
      Begin VB.CommandButton cmdPrnLabel 
         Caption         =   "Print Lab&el"
         CausesValidation=   0   'False
         Height          =   270
         Left            =   -68250
         TabIndex        =   69
         Top             =   2295
         Width           =   1125
      End
      Begin VB.TextBox TxtGLSalesID 
         Height          =   315
         Left            =   -73620
         TabIndex        =   33
         Top             =   735
         Width           =   1575
      End
      Begin VB.TextBox TxtGLConsID 
         Height          =   315
         Left            =   -73620
         TabIndex        =   32
         Top             =   1455
         Width           =   1575
      End
      Begin VB.TextBox TxtGLDiscID 
         Height          =   315
         Left            =   -73620
         TabIndex        =   31
         Top             =   1800
         Width           =   1575
      End
      Begin VB.TextBox TxtGLStaxID 
         Height          =   315
         Left            =   -73620
         TabIndex        =   30
         Top             =   2145
         Width           =   1575
      End
      Begin VB.TextBox TxtGLPurID 
         Height          =   315
         Left            =   -73620
         TabIndex        =   29
         Top             =   1110
         Width           =   1575
      End
      Begin VB.TextBox TxtSTaxReg 
         Alignment       =   1  'Right Justify
         Height          =   300
         Left            =   -73185
         TabIndex        =   28
         Top             =   1995
         Width           =   1770
      End
      Begin VB.TextBox TxtSTaxUnReg 
         Alignment       =   1  'Right Justify
         Height          =   315
         Left            =   -69645
         TabIndex        =   27
         Top             =   1965
         Width           =   1770
      End
      Begin VB.CommandButton CmdPrnDes 
         Caption         =   "Pri&nt Desc"
         CausesValidation=   0   'False
         Height          =   270
         Left            =   -69645
         TabIndex        =   70
         Top             =   2295
         Width           =   1125
      End
      Begin VSFlex7LCtl.VSFlexGrid grd 
         Height          =   2235
         Index           =   0
         Left            =   15
         TabIndex        =   34
         Top             =   360
         Width           =   7755
         _cx             =   13679
         _cy             =   3942
         _ConvInfo       =   1
         Appearance      =   1
         BorderStyle     =   1
         Enabled         =   -1  'True
         BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
            Name            =   "Calibri"
            Size            =   9.75
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
         FormatString    =   $"Fin_Item.frx":008C
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
      Begin VSFlex7LCtl.VSFlexGrid grd 
         Height          =   2235
         Index           =   1
         Left            =   -75000
         TabIndex        =   68
         Top             =   360
         Width           =   7755
         _cx             =   13679
         _cy             =   3942
         _ConvInfo       =   1
         Appearance      =   1
         BorderStyle     =   1
         Enabled         =   -1  'True
         BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
            Name            =   "Calibri"
            Size            =   9.75
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
         FormatString    =   $"Fin_Item.frx":00DB
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
      Begin VB.Label TxtGLSalesTitle 
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         Caption         =   "General Ledger Sales Title"
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -72000
         TabIndex        =   62
         Top             =   420
         Width           =   4620
      End
      Begin VB.Label TxtGLConsTitle 
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         Caption         =   "General Ledger Consumption Title"
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -72000
         TabIndex        =   61
         Top             =   1140
         Width           =   4620
      End
      Begin VB.Label TxtGLDiscTitle 
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         Caption         =   "General Ledger Discount Title"
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -72000
         TabIndex        =   60
         Top             =   1485
         Width           =   4620
      End
      Begin VB.Label TxtGLStaxTitle 
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         Caption         =   "General Ledger Sales Tax Title"
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -72000
         TabIndex        =   59
         Top             =   1830
         Width           =   4620
      End
      Begin VB.Label LblGLSalesID 
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "GL Sales ID :"
         Height          =   195
         Left            =   -74625
         TabIndex        =   58
         ToolTipText     =   "Clickk to repeate GL Integration ID to All fields"
         Top             =   525
         Width           =   945
      End
      Begin VB.Label Label24 
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "GL Cons ID :"
         Height          =   195
         Left            =   -74610
         TabIndex        =   57
         Top             =   1230
         Width           =   915
      End
      Begin VB.Label Label25 
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "GL Discount ID :"
         Height          =   195
         Left            =   -74865
         TabIndex        =   56
         Top             =   1575
         Width           =   1185
      End
      Begin VB.Label Label26 
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "GL S-Tax ID :"
         Height          =   195
         Left            =   -74655
         TabIndex        =   55
         Top             =   1905
         Width           =   975
      End
      Begin VB.Label Label15 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Opening Quantity :"
         Height          =   195
         Left            =   -74610
         TabIndex        =   54
         Top             =   825
         Width           =   1395
      End
      Begin VB.Label Label16 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Opening Values :"
         Height          =   195
         Left            =   -71325
         TabIndex        =   53
         Top             =   780
         Width           =   1650
      End
      Begin VB.Label Label17 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Current Quantity :"
         Height          =   195
         Left            =   -74610
         TabIndex        =   52
         Top             =   1170
         Width           =   1395
      End
      Begin VB.Label Label18 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Current Values :"
         Height          =   195
         Left            =   -71325
         TabIndex        =   51
         Top             =   1140
         Width           =   1650
      End
      Begin VB.Label TxtOQty 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -73185
         TabIndex        =   50
         Top             =   765
         Width           =   1770
      End
      Begin VB.Label TxtCQty 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -73185
         TabIndex        =   49
         Top             =   1110
         Width           =   1770
      End
      Begin VB.Label TxtCValue 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -69645
         TabIndex        =   48
         Top             =   1080
         Width           =   1770
      End
      Begin VB.Label TxtOValue 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -69645
         TabIndex        =   47
         Top             =   720
         Width           =   1770
      End
      Begin VB.Label Label20 
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "GL Pur ID :"
         Height          =   195
         Left            =   -74490
         TabIndex        =   46
         Top             =   855
         Width           =   795
      End
      Begin VB.Label TxtGLPurTitle 
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         Caption         =   "General Ledger Purchase Title"
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -72000
         TabIndex        =   45
         Top             =   795
         Width           =   4620
      End
      Begin VB.Label Label21 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Sales Tax Reg. %  :"
         Height          =   195
         Left            =   -74610
         TabIndex        =   44
         Top             =   2055
         Width           =   1395
      End
      Begin VB.Label Label22 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Sales Tax Un-Reg.  % :"
         Height          =   195
         Left            =   -71325
         TabIndex        =   43
         Top             =   2040
         Width           =   1650
      End
      Begin VB.Label TxtSCQty 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -73185
         TabIndex        =   42
         Top             =   840
         Width           =   1755
      End
      Begin VB.Label TxtSOQty 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -73185
         TabIndex        =   41
         Top             =   465
         Width           =   1755
      End
      Begin VB.Label Label36 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Current Quantity :"
         Height          =   195
         Left            =   -74535
         TabIndex        =   40
         Top             =   900
         Width           =   1320
      End
      Begin VB.Label Label37 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Opening Quantity :"
         Height          =   195
         Left            =   -74535
         TabIndex        =   39
         Top             =   525
         Width           =   1320
      End
      Begin VB.Label lblLastPurPer 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         ForeColor       =   &H00800000&
         Height          =   315
         Left            =   -69645
         TabIndex        =   38
         Top             =   1470
         Width           =   1770
      End
      Begin VB.Label Label35 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Last Pur % age :"
         Height          =   195
         Left            =   -71325
         TabIndex        =   37
         Top             =   1530
         Width           =   1650
      End
      Begin VB.Label TxtAverageCost 
         Alignment       =   1  'Right Justify
         BackColor       =   &H00E0E0E0&
         BorderStyle     =   1  'Fixed Single
         ForeColor       =   &H00C00000&
         Height          =   315
         Left            =   -73185
         TabIndex        =   36
         Top             =   1470
         Width           =   1770
      End
      Begin VB.Label Label19 
         Alignment       =   1  'Right Justify
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Average Cost :"
         Height          =   195
         Left            =   -74610
         TabIndex        =   35
         Top             =   1530
         Width           =   1395
      End
   End
   Begin VB.Label Label45 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Saved C&ost Price :"
      Height          =   195
      Left            =   15
      TabIndex        =   126
      Top             =   5145
      Width           =   1320
   End
   Begin VB.Label Label44 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "TP Rate :"
      Height          =   195
      Left            =   5985
      TabIndex        =   123
      Top             =   4860
      Width           =   690
   End
   Begin VB.Label Label43 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Sale Price WO GST :"
      Height          =   195
      Left            =   2895
      TabIndex        =   121
      Top             =   4830
      Width           =   1515
   End
   Begin VB.Label lblProfitPer 
      Alignment       =   2  'Center
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "%"
      ForeColor       =   &H00800000&
      Height          =   315
      Left            =   2790
      TabIndex        =   120
      Top             =   4440
      Width           =   690
   End
   Begin VB.Label Label38 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&WS Barcode ID :"
      Height          =   195
      Left            =   3930
      TabIndex        =   119
      Top             =   2175
      Width           =   1215
   End
   Begin VB.Label TxtTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Item Title"
      BeginProperty Font 
         Name            =   "Microsoft Sans Serif"
         Size            =   8.25
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00800000&
      Height          =   315
      Left            =   3090
      TabIndex        =   118
      Top             =   1050
      Width           =   4710
   End
   Begin VB.Label Label3 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Man&ual ID :"
      Height          =   195
      Left            =   510
      TabIndex        =   117
      Top             =   1815
      Width           =   825
   End
   Begin VB.Label Label27 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Country :"
      Height          =   195
      Left            =   3465
      TabIndex        =   116
      Top             =   2490
      Width           =   945
   End
   Begin VB.Label Label14 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Sa&les Price :"
      Height          =   195
      Left            =   3525
      TabIndex        =   115
      Top             =   4500
      Width           =   885
   End
   Begin VB.Label Label13 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&Reorder :"
      Height          =   195
      Left            =   405
      TabIndex        =   114
      Top             =   3195
      Width           =   930
   End
   Begin VB.Label Label12 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Critital Level :"
      Height          =   195
      Left            =   3465
      TabIndex        =   113
      Top             =   3195
      Width           =   945
   End
   Begin VB.Label Label11 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Min. Level :"
      Height          =   195
      Left            =   405
      TabIndex        =   112
      Top             =   2835
      Width           =   930
   End
   Begin VB.Label Label10 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Max. Level :"
      Height          =   195
      Left            =   3465
      TabIndex        =   111
      Top             =   2835
      Width           =   945
   End
   Begin VB.Label TxtUOMTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Unit"
      ForeColor       =   &H00800000&
      Height          =   330
      Left            =   3105
      TabIndex        =   110
      Top             =   2100
      Width           =   555
   End
   Begin VB.Label Label8 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "C&ost Price :"
      Height          =   195
      Left            =   525
      TabIndex        =   109
      Top             =   4500
      Width           =   810
   End
   Begin VB.Label Label7 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "UOM ID :"
      Height          =   195
      Left            =   405
      TabIndex        =   108
      Top             =   2160
      Width           =   930
   End
   Begin VB.Label Label6 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "OEM/Part/Brand :"
      Height          =   195
      Left            =   3840
      TabIndex        =   107
      Top             =   1455
      Width           =   1305
   End
   Begin VB.Label Label5 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Short Name :"
      Height          =   195
      Left            =   405
      TabIndex        =   105
      Top             =   1455
      Width           =   930
   End
   Begin VB.Label LblItem 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&Item ID :"
      Height          =   195
      Left            =   735
      TabIndex        =   104
      Top             =   1110
      Width           =   600
   End
   Begin VB.Label Label1 
      Alignment       =   2  'Center
      BackColor       =   &H00C98A45&
      Caption         =   "Records"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   300
      Left            =   2535
      TabIndex        =   103
      Top             =   600
      Width           =   1245
   End
   Begin VB.Label TxtRecCount 
      Alignment       =   2  'Center
      BackColor       =   &H00F2CD6C&
      Caption         =   "000"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   300
      Left            =   3795
      TabIndex        =   102
      Top             =   600
      Width           =   1245
   End
   Begin VB.Label LblStatus 
      Alignment       =   2  'Center
      BackColor       =   &H00F2CD6C&
      Caption         =   "Ready"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   300
      Left            =   1275
      TabIndex        =   101
      Top             =   600
      Width           =   1245
   End
   Begin VB.Label Label4 
      Alignment       =   2  'Center
      BackColor       =   &H00C98A45&
      Caption         =   "Status"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H8000000E&
      Height          =   300
      Left            =   15
      TabIndex        =   100
      Top             =   600
      Width           =   1245
   End
   Begin VB.Label Line2 
      Alignment       =   2  'Center
      BackColor       =   &H00C98A45&
      Caption         =   "Item Info"
      BeginProperty Font 
         Name            =   "Arial Black"
         Size            =   15.75
         Charset         =   0
         Weight          =   900
         Underline       =   0   'False
         Italic          =   -1  'True
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H8000000E&
      Height          =   495
      Left            =   0
      TabIndex        =   99
      Top             =   30
      Width           =   8010
   End
   Begin VB.Label Line3 
      BackColor       =   &H00FFFFFF&
      ForeColor       =   &H00000000&
      Height          =   30
      Left            =   30
      TabIndex        =   98
      Top             =   540
      Width           =   7950
   End
   Begin VB.Label Label42 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "GST Amt :"
      Height          =   195
      Left            =   5985
      TabIndex        =   76
      Top             =   5175
      Width           =   690
   End
   Begin VB.Label Label41 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Cost &WO GST :"
      Height          =   195
      Left            =   225
      TabIndex        =   74
      Top             =   4830
      Width           =   1110
   End
   Begin VB.Label Label40 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Market &Price :"
      Height          =   195
      Left            =   3420
      TabIndex        =   9
      Top             =   5145
      Width           =   990
   End
   Begin VB.Label Line1 
      BackColor       =   &H00FFFFFF&
      ForeColor       =   &H00000000&
      Height          =   30
      Left            =   30
      TabIndex        =   67
      Top             =   15
      Width           =   7950
   End
   Begin VB.Label Label2 
      Alignment       =   2  'Center
      BackColor       =   &H00C98A45&
      Caption         =   "Last ID"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   300
      Left            =   5055
      TabIndex        =   66
      Top             =   600
      Width           =   1245
   End
   Begin VB.Label TxtLastID 
      Alignment       =   2  'Center
      BackColor       =   &H00F2CD6C&
      Caption         =   "000000"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   9.75
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   300
      Left            =   6315
      TabIndex        =   65
      Top             =   600
      Width           =   1680
   End
   Begin VB.Label Label9 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Remarks :"
      Height          =   195
      Left            =   405
      TabIndex        =   11
      Top             =   5460
      Width           =   930
   End
   Begin VB.Label LblCoTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Title of Company"
      ForeColor       =   &H00800000&
      Height          =   315
      Left            =   2160
      TabIndex        =   64
      Top             =   5745
      Width           =   5760
   End
   Begin VB.Label Label23 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Company :"
      Height          =   195
      Left            =   405
      TabIndex        =   16
      Top             =   5805
      Width           =   930
   End
   Begin VB.Label Label28 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "&Barcode ID :"
      Height          =   195
      Left            =   4245
      TabIndex        =   1
      Top             =   1815
      Width           =   900
   End
   Begin VB.Label Label29 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "Unit of Packing :"
      Height          =   195
      Left            =   3225
      TabIndex        =   13
      Top             =   5460
      Width           =   1185
   End
   Begin VB.Label LblCountryTitle 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Country of Origin"
      ForeColor       =   &H00800000&
      Height          =   330
      Left            =   5175
      TabIndex        =   63
      Top             =   2422
      Width           =   2625
   End
   Begin VB.Label Label34 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "W.S Price :"
      Height          =   195
      Left            =   5985
      TabIndex        =   8
      Top             =   4515
      Width           =   690
   End
   Begin VB.Label Label39 
      Alignment       =   1  'Right Justify
      AutoSize        =   -1  'True
      BackStyle       =   0  'Transparent
      Caption         =   "No of Pur :"
      Height          =   195
      Left            =   5985
      TabIndex        =   15
      Top             =   5460
      Width           =   690
   End
End
Attribute VB_Name = "Fin_Item"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit
Private RsDummy As New ADODB.Recordset
Private mLastID As Double
Private cRecTotal, cLastId As Integer
Private cFoundFlag As Boolean
Private cItemPrice As Boolean

Private Sub chkBarPrint_Click()
    txtBarcodeID.SetFocus
End Sub

Private Sub chkPromotion_Click()

'If cFoundFlag = True Then Exit Sub

'If MsgBox("Are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
'
'
'End If


End Sub

Private Sub chkPromotion_KeyDown(Keycode As Integer, Shift As Integer)
    If vbKeySpace = True Then
    
        Dim intHoldValue As Integer
        
        intHoldValue = chkPromotion.Value
        
            If MsgBox("Are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
                
                If chkPromotion.Value = 0 Then
                    chkPromotion.Value = 1
                Else
                    chkPromotion.Value = 0
                End If
                
                Exit Sub
            Else
                chkPromotion.Value = intHoldValue
            End If
    End If
End Sub

Private Sub chkPromotion_MouseDown(Button As Integer, Shift As Integer, X As Single, Y As Single)

Dim intHoldValue As Integer

intHoldValue = chkPromotion.Value

    If MsgBox("Are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
        
        If chkPromotion.Value = 0 Then
            chkPromotion.Value = 1
        Else
            chkPromotion.Value = 0
        End If
        
        Exit Sub
    Else
        chkPromotion.Value = intHoldValue
    End If

End Sub


Private Sub CmdCategory_Click()
    Fin_Cat.Show vbModal, Me
End Sub

Private Sub CmdManual_Click()
Dim cSQL As String
Dim Rs As New ADODB.Recordset

    If txtManualID.Enabled = False Then
        MsgBox "This Option is available only for new items.", vbOKOnly
        Exit Sub
    End If
    
    cSQL = "SELECT max(manualid) as manualid FROM v_fin_item "

    With Rs
        .Open cSQL, Con, adOpenKeyset, adLockPessimistic
        If Not (.EOF And .BOF) Then
            txtManualID.Text = CDbl(IIf(IsNull(Rs!manualid) = True, 0, Rs!manualid)) + 1
        Else
            txtManualID.Text = 1
        End If
        .Close
    End With
    '
    TxtUOMID.Text = 1
    TxtUOMID_Validate False
    '
    TxtCountryID.Text = 1
    TxtCountryID_Validate False
    '
    TxtCo.Text = 1
    TxtCo_Validate False


    TxtGLSalesID.Text = "30010001"
    TxtGLPurID.Text = "30010001"
    TxtGLConsID.Text = "30010001"
    TxtGLDiscID.Text = "30010001"
    TxtGLStaxID.Text = "30010001"
    

End Sub

Private Sub cmdOpening_Click()
    Fin_OpBal.Show vbModal, Me
    Fin_OpBal.TxtID.Text = mLastID
'    Fin_OpBalStore.Show vbModal, Me
'    Fin_OpBalStore.TxtID.Text = mLastID
'
End Sub

Private Sub cmdPrintRail_Click()

Dim X As Integer


If MsgBox("Do you want to take a print :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
        
        SQL = "select * from v_fin_item where item_id = " & TxtID.Text
        cSelcriteria = SQL
        
        'For X = 1 To txtNoOf
        
            With LstInvStore_short_PrnDescRailCard
            'With LstInvStore_short_PrnDescRailCardSm
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
                .PageSettings.LeftMargin = 0 '150 ' ½ inch left margin
                .PageSettings.RightMargin = 0 ' ½ inch right margin
                '.PageSettings.PaperWidth = 0 '2400  '2163 '72.1
                '.PageSettings.PaperHeight = 0 '2000 '1617 '10276
               ' Printing Orientation Portrait/Landscape
               ''iOrientationSav = Printer.Orientation
                .Printer.Orientation = ddOPortrait
                .Printer.Copies = 1 'txtNoOf '2
                .PrintReport False
            End With
            'Set LstInvStore_short_PrnDescRailCard = Nothing
            Set LstInvStore_short_PrnDescRailCard = Nothing
            
Else
    
    SQL = "select * from v_fin_item where item_id = " & TxtID.Text
    cSelcriteria = SQL
    
    
    With LstInvStore_short_PrnDescRailCard
        '.PageSettings.TopMargin = 50
        .PageSettings.BottomMargin = 0 ' 1 inch bottom margin
        .PageSettings.TopMargin = 0 '300 ' 1 inch top margin
        .PageSettings.LeftMargin = 0 '450 '150 ' ½ inch left margin
        .PageSettings.RightMargin = 0 ' ½ inch right margin
        
'        .PageSettings.PaperWidth = 6000 '2163 '5963 '72.1
'        .PageSettings.PaperHeight = 2200  '2917 '10276
    End With
    
    'LstInvStore_short_PrnDescRailCard.Show vbModal, Me
    LstInvStore_short_PrnDescRailCard.Show vbModal, Me

End If
    
        Call clearform
        txtBarcodeID.Text = ""
        txtBarcodeID.SetFocus
End Sub

Private Sub CmdPrnDes_Click()


'        For i = 0 To UBound(p_strQueryArray)
'            If p_strQueryArray(i) <> "" Then
'                .CommandText = p_strQueryArray(i)
'                'Debug.Print p_strQueryArray(i)
'                .Execute
'            End If
'        Next



Dim X As Integer



If MsgBox("Do you want to take a print :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
        
        SQL = "select * from v_fin_item where item_id = " & TxtID.Text
        cSelcriteria = SQL
        
        If MsgBox("Do you want to hide price :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
            PrintPriceZero = True
        Else
            PrintPriceZero = False
        End If
        'For X = 1 To txtNoOf
        
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
                .PageSettings.LeftMargin = 0 '150 ' ½ inch left margin
                .PageSettings.RightMargin = 0 ' ½ inch right margin
                .PageSettings.PaperWidth = 2163  '2163 '72.1
                .PageSettings.PaperHeight = 1617 '1617 '10276
               ' Printing Orientation Portrait/Landscape
               ''iOrientationSav = Printer.Orientation
                .Printer.Orientation = ddOPortrait
                .Printer.Copies = txtNoOf '1
                .PrintReport False
            End With
            Set LstInvStore_short_PrnDesc = Nothing
            Call clearform
            
            If chkFocusManBar.Value = 1 Then
                txtBarcodeID.Text = "0"
                txtBarcodeID.SetFocus
'                txtBarcodeID.SelText(
            Else
                txtManualID.Text = "0"
                txtManualID.SetFocus
'                txtManualID.SelText
            End If
        'Next
Else
    
    SQL = "select * from v_fin_item where item_id = " & TxtID.Text
    cSelcriteria = SQL
    
    If MsgBox("Do you want to hide price :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
        PrintPriceZero = True
    Else
        PrintPriceZero = False
    End If
    
    With LstInvStore_short_PrnDesc
        '.PageSettings.TopMargin = 50
        .PageSettings.PaperWidth = 2163 '5963 '72.1
        .PageSettings.PaperHeight = 1617 '2917 '10276
    End With
    
    
    LstInvStore_short_PrnDesc.Show vbModal, Me
    'MKB 14 03 2024
    'txtManualID.SetFocus
    Call CmdClear_Click
    
'    If chkFocusManBar.Value = 1 Then
'        txtBarcodeID.Text = "0"
'        txtBarcodeID.SetFocus
'    Else
'        txtManualID.SetFocus
'    End If
    

End If
    
End Sub

Private Sub Command1_Click()

End Sub


Private Sub CmdPrnDesExp_Click()
    

Dim X As Integer

If MsgBox("Do you want to take a print :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then

        If MsgBox("Do you want to hide price :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
            PrintPriceZero = True
        Else
            PrintPriceZero = False
        End If

        
        SQL = "select * from v_fin_item where item_id = " & TxtID.Text
        cSelcriteria = SQL
        
        'For X = 1 To txtNoOf
        
            With LstInvStore_short_PrnDescExp
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
                .PageSettings.LeftMargin = 0 '150 ' ½ inch left margin
                .PageSettings.RightMargin = 0 ' ½ inch right margin
                .PageSettings.PaperWidth = 2163 '2400  '2163 '72.1
                .PageSettings.PaperHeight = 2000 '1617 '2000 '1617 '10276
               ' Printing Orientation Portrait/Landscape
               ''iOrientationSav = Printer.Orientation
                .Printer.Orientation = ddOPortrait
                .Printer.Copies = txtNoOf '2
                .PrintReport False
            End With
            Set LstInvStore_short_PrnDescExp = Nothing
            Call clearform
            txtBarcodeID.Text = ""
            'txtBarcodeID.SetFocus
            txtManualID.SetFocus
        'Next
Else
    
    If MsgBox("Do you want to hide price :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
        PrintPriceZero = True
    Else
        PrintPriceZero = False
    End If
    
    SQL = "select * from v_fin_item where item_id = " & TxtID.Text
    cSelcriteria = SQL
    
    With LstInvStore_short_PrnDescExp
        '.PageSettings.TopMargin = 50
        .PageSettings.PaperWidth = 2163 '5963 '72.1
        .PageSettings.PaperHeight = 2000 '2917 '10276
    End With
   LstInvStore_short_PrnDescExp.Show vbModal, Me
    
'    With LstInvStore_short_PrnDescRailCard
'        '.PageSettings.TopMargin = 50
'
'        .PageSettings.BottomMargin = 0 ' 1 inch bottom margin
'        .PageSettings.TopMargin = 0 '300 ' 1 inch top margin
'        .PageSettings.LeftMargin = 0 '450 '150 ' ½ inch left margin
'        .PageSettings.RightMargin = 0 ' ½ inch right margin
'
'    End With
'
'    LstInvStore_short_PrnDescRailCard.Show vbModal, Me

End If
    
    
    

End Sub

Private Sub cmdPrnLabel_Click()

    SQL = "select * from v_fin_item where item_id = " & TxtID.Text
    cSelcriteria = SQL
    
    'With LstInvStore_short_PrnDesc
    With LstInvStore_short_PrnDescRate
        .PageSettings.TopMargin = 50
        .PageSettings.PaperWidth = 5963 '72.1
        .PageSettings.PaperHeight = 2917 '10276
    End With
    
    
    LstInvStore_short_PrnDescRate.Show vbModal, Me
End Sub


Private Sub cmdRailCardSM_Click()

Dim X As Integer



If MsgBox("Do you want to take a print :  are you sure ? ", vbInformation + vbYesNo, "Item Setup") = vbYes Then
        
        SQL = "select * from v_fin_item where item_id = " & TxtID.Text
        cSelcriteria = SQL
        
      

        With LstInvStore_short_PrnDescRailCardSm
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
            .PageSettings.LeftMargin = 0 '150 ' ½ inch left margin
            .PageSettings.RightMargin = 0 ' ½ inch right margin
            '.PageSettings.PaperWidth = 0 '2400  '2163 '72.1
            '.PageSettings.PaperHeight = 0 '2000 '1617 '10276
           ' Printing Orientation Portrait/Landscape
           ''iOrientationSav = Printer.Orientation
            .Printer.Orientation = ddOPortrait
            .Printer.Copies = txtNoOf '2
            .PrintReport False
        End With
        'Set LstInvStore_short_PrnDescRailCard = Nothing
        Set LstInvStore_short_PrnDescRailCardSm = Nothing
            
Else
    
    SQL = "select * from v_fin_item where item_id = " & TxtID.Text
    cSelcriteria = SQL
    
    
    With LstInvStore_short_PrnDescRailCardSm
        '.PageSettings.TopMargin = 50
        .PageSettings.BottomMargin = 0 ' 1 inch bottom margin
        .PageSettings.TopMargin = 0 '300 ' 1 inch top margin
        .PageSettings.LeftMargin = 0 '450 '150 ' ½ inch left margin
        .PageSettings.RightMargin = 0 ' ½ inch right margin
        
'        .PageSettings.PaperWidth = 6000 '2163 '5963 '72.1
'        .PageSettings.PaperHeight = 2200  '2917 '10276
    End With
    
    'LstInvStore_short_PrnDescRailCard.Show vbModal, Me
    LstInvStore_short_PrnDescRailCardSm.Show vbModal, Me

End If
            Call clearform
            txtBarcodeID.Text = ""
            txtBarcodeID.SetFocus
End Sub




Private Sub Form_Activate()
    Call FormDisplaySetting(Me)
    
    If blnItemActive = True Then
        Call CmdManual_Click
        Call TxtID_Validate(False)
    End If
    'New MKB
    If txtManualID.Enabled = True Then
        txtManualID.SetFocus
    End If
    With grd(0)
        .Cols = 5
        .TextMatrix(0, 0) = "Pur.#"
        .TextMatrix(0, 1) = "Date"
        .ColWidth(1) = 1200
        .TextMatrix(0, 2) = "Supplier"
        .ColWidth(2) = 3300
        .TextMatrix(0, 3) = "Qty"
        .ColWidth(3) = 1000
        .TextMatrix(0, 4) = "Rate"
        .ColWidth(4) = 1000
    End With
    With grd(1)
        .Cols = 5
        .TextMatrix(0, 0) = "Inv.#"
        .TextMatrix(0, 1) = "Date"
        .ColWidth(1) = 1200
        .TextMatrix(0, 2) = "Customer"
        .ColWidth(2) = 3300
        .TextMatrix(0, 3) = "Qty"
        .ColWidth(3) = 1000
        .TextMatrix(0, 4) = "Rate"
        .ColWidth(4) = 1000
    End With

    
End Sub

Private Sub Form_Click()

'Dim cSQL As String
'Dim Rs As New ADODB.Recordset
'
'    cSQL = "SELECT max(manualid) as manualid FROM v_fin_item "
'
'    With Rs
'        .Open cSQL, Con, adOpenKeyset, adLockPessimistic
'        If Not (.EOF And .BOF) Then
'            txtManualID.Text = CDbl(IIf(IsNull(Rs!manualid) = True, 0, Rs!manualid)) + 1
'        Else
'            txtManualID.Text = 1
'        End If
'        .Close
'    End With
'    '
'    TxtUOMID.Text = 1
'    TxtUOMID_Validate False
'    '
'    TxtCountryID.Text = 1
'    TxtCountryID_Validate False
'    '
'    TxtCo.Text = 1
'    TxtCo_Validate False
'
'
'    TxtGLSalesID.Text = "30010001"
'    TxtGLPurID.Text = "30010001"
'    TxtGLConsID.Text = "30010001"
'    TxtGLDiscID.Text = "30010001"
'    TxtGLStaxID.Text = "30010001"
'
End Sub


Private Sub Form_KeyDown(Keycode As Integer, Shift As Integer)

If UCase(cLoginName) = "SA" Or LCase(cLoginName) = "sa" Then
    If txtManualID = "" Or txtManualID = "0" Then Exit Sub
    If Keycode = vbKeyF5 Then
        With FrmTestForm
            .txtQuery = "select * from v_log_data where manualid = " & txtManualID & " order by sdate desc"
            blnExecuteClickButton = True
            .Show vbModal, Me
        End With
    End If
End If

End Sub

Private Sub Form_Paint()
'    If Not TxtID.Text = "0" Then
'        TxtID_Validate (False)
'        TxtCost_Price.SetFocus
'    End If
    
End Sub

Private Sub Label19_Click()
Dim Rs As New ADODB.Recordset

'    'SQL = "select (sum(pur_amt) / sum(qty)) as AvgRate from Fin_Pur_D where item_id = " & TxtID.Text
'    SQL = "select ((sum(PUR_AMT) - SUM(DISC_AMT))/ sum(qty)) as AvgRate from Fin_Pur_D where item_id = " & TxtID.Text
'    Set Rs = FetchAll(SQL)
'    If IsNull(Rs!avgrate) = False Then
'        TxtAverageCost.Caption = Rs!avgrate
'        'lblProfitPer.Caption = Format((100 - ((Val(TxtAverageCost.Caption) / Val(TxtSales_Price)) * 100)), "########.00")
'        lblProfitPer.Caption = Format((100 - ((Val(TxtCost_Price.Text) / Val(TxtSales_Price)) * 100)), "########.00")
'    Else
'        TxtAverageCost.Caption = "0.00"
'    End If
'
'    Set Rs = Nothing
    
    lblProfitPer.Caption = Format((100 - ((Val(TxtCost_Price.Text) / Val(TxtSales_Price)) * 100)), "########.00")
End Sub





Private Sub txtBarcodeID_GotFocus()


With txtBarcodeID
    .SelStart = 0
    .SelLength = Len(.Text)
End With


End Sub

Private Sub txtBarcodeID_Validate(Cancel As Boolean)
Dim cSQL As String
Dim Rs As New ADODB.Recordset

If Not TxtID.Text = "" Then Exit Sub
If txtBarcodeID.Text = "" Or txtBarcodeID.Text = "0" Then Exit Sub
'If Not txtWSBarcodeid.Text = "" Or Not txtWSBarcodeid.Text = "0" Then Exit Sub

'If Not txtManualID.Text = "" Or Not txtManualID.Text = "0" Then Exit Sub


'cSQL = "SELECT * FROM v_fin_item WHERE barcodeid = '" & Trim(txtBarcodeID.Text) & "'"
cSQL = "SELECT * FROM fin_item WHERE barcodeid = '" & Trim(txtBarcodeID.Text) & "'"

    Set Rs = FetchAll(cSQL)
    With Rs
        '.Open cSQL, Con, adOpenKeyset, adLockPessimistic
        If Not (.EOF And .BOF) Then
            'MsgBox "Barcode already exisit '" & Rs!Item_ID & "' ," & Rs!Item_Title
            TxtID.Text = !Item_ID
            Call TxtID_Validate(False)
        End If
        .Close
    End With
End Sub

Private Sub TxtCo_DblClick()
  cSQLId = "COID"
  cSelFormId = "COID_FIN_ITEM"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub TxtCo_KeyDown(Keycode As Integer, Shift As Integer)
    On Error GoTo errhandler
        If Keycode = 113 Then
            Call TxtCo_DblClick
        End If
    Exit Sub
errhandler:
        MsgBox Err.Description, vbInformation, cSelFormId
        Err.Clear
End Sub
Private Sub TxtCo_Validate(Cancel As Boolean)
   If Len(Trim(TxtCo)) = 0 Or Val(TxtCo) = 0 Then
        Exit Sub
   End If
   Screen.MousePointer = vbHourglass
   SQL = "SELECT * FROM Co WHERE Co_id = " & Val(TxtCo)
   Set RsDummy = FetchAll(SQL)
   If Not (RsDummy.EOF And RsDummy.BOF) Then
     lblCoTitle.Caption = "" & RsDummy!co_title
   Else
      Screen.MousePointer = vbDefault
      MsgBox "Company ID not found ... ", vbInformation
      Cancel = True
      RsDummy.Close
      TxtCo.SetFocus
      Exit Sub
   End If
   RsDummy.Close
   Screen.MousePointer = vbDefault
End Sub

Private Sub TxtCountryID_KeyDown(Keycode As Integer, Shift As Integer)
    On Error GoTo errhandler
        If Keycode = 113 Then
            Call TxtCountryID_DblClick
        End If
    Exit Sub
errhandler:
        MsgBox Err.Description, vbInformation, cSelFormId
        Err.Clear
End Sub

Private Sub TxtGLConsID_KeyDown(Keycode As Integer, Shift As Integer)
On Error GoTo errhandler
    If Keycode = 113 Then
        Call TxtGLConsID_DblClick
    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear

End Sub

Private Sub TxtGLDiscID_KeyDown(Keycode As Integer, Shift As Integer)
On Error GoTo errhandler
    If Keycode = 113 Then
        Call TxtGLDiscID_DblClick
    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear

End Sub

Private Sub TxtGLPurID_KeyDown(Keycode As Integer, Shift As Integer)
On Error GoTo errhandler
    If Keycode = 113 Then
        Call TxtGLPurID_DblClick
    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear
End Sub

Private Sub TxtGLSalesID_KeyDown(Keycode As Integer, Shift As Integer)
On Error GoTo errhandler
    If Keycode = 113 Then
        Call TxtGLSalesID_DblClick
    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear
End Sub

Private Sub TxtGLStaxID_KeyDown(Keycode As Integer, Shift As Integer)
On Error GoTo errhandler
    If Keycode = 113 Then
        Call TxtGLStaxID_DblClick
    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear

End Sub

Private Sub TxtID_KeyDown(Keycode As Integer, Shift As Integer)
On Error GoTo errhandler
    If Keycode = 114 Then
        Call LblItem_Click
    ElseIf Keycode = 115 Then 'F4
        TxtID.Text = mLastID
    ElseIf Keycode = 116 Then 'F5
        TxtID.Text = mLastID + 1
    ElseIf Keycode = 117 Then 'F6
        With FrmSalesTransRpt
            If Not TxtID.Text = "" Then
                blnAllowFrm = True
                .CboReport.ListIndex = 2
                .TxtStartCode = TxtID.Text
                .TxtEndCode = TxtID.Text
                .Show vbModal, Me
                blnAllowFrm = False
            End If
        End With
    Else
       If Keycode = 113 Then
        Call TxtID_DblClick
        TxtID_Validate (False)
       End If
    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear
End Sub

Private Sub LblItem_Click()
  cSQLId = "ITEMID"
  cSelFormId = "ITEMID"
  Fin_Auto.Show vbModal, Me
  TxtID.SetFocus
End Sub

Private Sub LblGLSalesID_Click()
    TxtGLPurID = TxtGLSalesID
    TxtGLPurTitle = TxtGLSalesTitle
    '
    TxtGLConsID = TxtGLSalesID
    TxtGLConsTitle = TxtGLSalesTitle
    '
    TxtGLDiscID = TxtGLSalesID
    TxtGLDiscTitle = TxtGLSalesTitle
    '
    TxtGLStaxID = TxtGLSalesID
    TxtGLStaxTitle = TxtGLSalesTitle
End Sub

Private Sub TxtCountryID_DblClick()
  cSQLId = "COUNTRYID"
  cSelFormId = "CID_FIN_ITEM"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub TxtCountryID_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, False)
''        Dim strvalid As String
''        strvalid = "0123456789"
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtCountryID))
''            If mLen = 0 Then
''                TxtCountryID.Text = ""
''            Else
''                TxtCountryID.Text = Left(Trim(TxtCountryID), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub CmdDelete_Click()
    ' Item
    Dim mTotal As Long
    Screen.MousePointer = vbHourglass
    ' Check Opening Balance
    SQL = "SELECT * FROM fin_item WHERE ITEM_ID = " & Val(TxtID)
    Set RsDummy = FetchAll(SQL)
    If Not (RsDummy.EOF And RsDummy.BOF) Then
        If RsDummy!Cqty > 0 Or RsDummy!CAMT > 0 Then
            Screen.MousePointer = vbDefault
            MsgBox "Cannot Delete, Item Contain Balance Quantity/Amount ...", vbCritical, cSelFormId
            RsDummy.Close
            Exit Sub
        End If
    End If
    RsDummy.Close
    ' Check Transactions in Fin-Ledger
    ' As all production, Sales Invoice etc are present in Fin-Inv Ledger
    SQL = "SELECT * FROM fin_ldgr WHERE ITEM_ID = " & Val(TxtID)
    Set RsDummy = FetchAll(SQL)
    If Not (RsDummy.EOF And RsDummy.BOF) Then
        RsDummy.MoveLast
        mTotal = RsDummy.RecordCount
        Screen.MousePointer = vbDefault
        MsgBox "Cannot Delete, Item Contain transaction(s)." & Chr(13) & " Total Transaction(s) = " & Trim(str(mTotal)), vbCritical
        RsDummy.Close
        Exit Sub
    End If
    If MsgBox("Deleting Item ID:  are you sure ? ", vbInformation + vbYesNo, "Chart of Accounts") = vbYes Then
           Screen.MousePointer = vbHourglass
           SQL = "delete from FIN_CAT where ITEM_ID = " & Val(TxtID)
           Con.Execute SQL
           '
           SQL = "delete from fin_item where ITEM_ID = " & Val(TxtID)
           Con.Execute SQL
    Else
           Screen.MousePointer = vbDefault
           Exit Sub
    End If
    Screen.MousePointer = vbDefault
    Call clearform
End Sub

Private Sub cmdPrint_Click()
Call Calc_TB_Month
End Sub
Private Sub CmdSave_Click()
     ' Validity checks
     If Val(TxtID.Text) = 0 Then
        MsgBox "Invalid Item ID:  Blank or Zeror ID not allowed .... ", vbCritical, cSelFormId
        TxtID.Enabled = True
        TxtID.SetFocus
        Exit Sub
     End If
     If Val(TxtUOMID.Text) = 0 Then
        MsgBox "Invalid:  Blank UOM ID not allowed .... ", vbCritical, cSelFormId
        TxtUOMID.SetFocus
        Exit Sub
     End If
     If Val(TxtCountryID.Text) = 0 Then
        MsgBox "Invalid:  Blank Country ID not allowed .... ", vbCritical, cSelFormId
        TxtCountryID.SetFocus
        Exit Sub
     End If
     '
     If Len(Trim(TxtGLSalesID.Text)) = 0 Then
        MsgBox "Invalid:  Blank GL Sales ID not allowed .... ", vbCritical, cSelFormId
        TxtGLSalesID.SetFocus
        Exit Sub
     End If
     If Len(Trim(TxtGLConsID.Text)) = 0 Then
        MsgBox "Invalid:  Blank GL Consumption ID not allowed .... ", vbCritical, cSelFormId
        TxtGLConsID.SetFocus
        Exit Sub
     End If
     If Len(Trim(TxtGLDiscID.Text)) = 0 Then
        MsgBox "Invalid:  Blank GL Discount ID not allowed .... ", vbCritical, cSelFormId
        TxtGLDiscID.SetFocus
        Exit Sub
     End If
     If Len(Trim(TxtGLStaxID.Text)) = 0 Then
        MsgBox "Invalid:  Blank GL Sales Tax ID not allowed .... ", vbCritical, cSelFormId
        TxtGLStaxID.SetFocus
        Exit Sub
     End If
     If Val(TxtMin_Level) > Val(TxtMax_Level) Then
        MsgBox "Invalid:  Min Level Greater Than Max. Level .... ", vbCritical, cSelFormId
        TxtMin_Level.SetFocus
        Exit Sub
     End If
     If Val(TxtCo) = 0 Then
        MsgBox "Invalid:  Company ID .... ", vbCritical, cSelFormId
        TxtCo.SetFocus
        Exit Sub
     End If
     
     If Len(Trim(TxtRemarks)) = 0 Then
        TxtRemarks.Text = "Nil"
     End If
     If Len(Trim(TxtOEM)) = 0 Then
        TxtOEM.Text = "Nil"
     End If
     If Len(Trim(TxtShortName)) = 0 Then
        TxtShortName.Text = "Nil"
     End If
     'Hold Old data
     
'     Dim RsOld As New ADODB.Recordset
     
     Screen.MousePointer = vbHourglass
        SQL = "SELECT * FROM fin_item WHERE item_id = " & Val(TxtID)
        Set RsOld = FetchAll(SQL)
        If (RsOld.EOF And RsOld.BOF) Then
'            Exit Sub
        End If

     Screen.MousePointer = vbNormal
     'End Hold Data
     
     
     Screen.MousePointer = vbHourglass
     SQL = "SELECT * FROM fin_item WHERE item_id = " & Val(TxtID)
     Set Rs = FetchAll(SQL)
     If Not (Rs.EOF And Rs.BOF) Then
        'rs.edit
     Else
        cRecTotal = cRecTotal + 1
        Rs.AddNew
        Rs("item_id") = Val(TxtID)
     End If
     '
     Rs!Item_Title = "" & TxtTitle.Caption
     Rs!item_short = "" & TxtShortName.Text
     Rs!Ac_Level = 4
     Rs!ed_status = ChkEDStatus.Value
     'RS!commallow = chkCommission.Value
     Rs!item_oem = Trim(TxtOEM)
     Rs!manualid = Val(txtManualID)
     Rs!barcodeid = Val(txtBarcodeID)
     Rs!barcodeid_ws = Val(txtWSBarcodeid)
     Rs!visacard_rate = Val(txtVisaCardRate)
     Rs!uom_id = Val(TxtUOMID)
     Rs!country_id = Val(TxtCountryID)
     Rs!item_nature = CboNature.ListIndex
     '
     Rs!Min_Level = Val(TxtMin_Level)
     Rs!Max_Level = Val(TxtMax_Level)
     Rs!RO_qty = Val(TxtRO_Qty)
     Rs!critical_level = Val(TxtCritical_Level)
     '
     'Store Stock
     Rs!Min_Level1 = Val(TxtMin_Level1)
     Rs!Max_Level1 = Val(TxtMax_Level1)
     Rs!RO_qty1 = Val(TxtRO_Qty1)
     Rs!critical_level1 = chkPromotion.Value 'Val(TxtCritical_Level1)
     
     '
     Rs!oqty1 = Val(TxtSalesPWoGST)
     Rs!sales_Rate = Val(TxtSales_Price)
     Rs!cost_Rate = Val(TxtCost_Price)
     Rs!disc_p1 = Val(TxtMarket_Price)
     Rs!disc_p2 = 0
     Rs!disc_p3 = 0
     Rs!disc_p4 = Val(txtWSPrice.Text)
     Rs!gl_sales_id = Val(TxtGLSalesID)
     Rs!gl_pur_id = Val(TxtGLPurID)
     Rs!gl_cons_id = Val(TxtGLConsID)
     Rs!gl_disc_id = Val(TxtGLDiscID)
     Rs!gl_stax_id = Val(TxtGLStaxID)
     Rs!STAX_REG = Val(TxtSTaxReg)
     Rs!STAX_UNREG = Val(TxtSTaxUnReg)
     Rs!remarks = TxtRemarks
     Rs!co_id = Val(TxtCo)
        dbdebug = 3
        Call SaveRs(Rs)
        
        Dim X As Integer
        
        
    If Not (RsOld.EOF And RsOld.BOF) Then
        strStr = ""
        X = 0
        For X = 0 To RsOld.Fields().count - 1
'            RsOld.Fields (X)
            
            If Not RsOld.Fields(X) = Rs.Fields(X) Then
            
                Select Case UCase(Rs.Fields(X).NAME)
                    Case "DISC_P4"  'Whole sale rate
                        If Len(strStr) = 0 Then strStr = strStr & "MANUAL ID. " & RsOld!manualid & vbCrLf & _
                                            "ITEM " & vbCrLf & RsOld!Item_Title & vbCrLf & _
                                            "------" & vbCrLf
                        
                        strStr = strStr & "WS RATE" & vbCrLf & _
                                    RsOld.Fields(X) & vbCrLf & _
                                    Rs.Fields(X) & vbCrLf
                                    
                    Case "VISACARD_RATE"    'Packing unit
                        If Len(strStr) = 0 Then strStr = strStr & "MANUAL ID." & RsOld!manualid & vbCrLf & _
                                                    "ITEM " & vbCrLf & RsOld!Item_Title & vbCrLf & _
                                            "------" & vbCrLf
                            
                        
                        strStr = strStr & "PACK UNIT" & vbCrLf & _
                                    RsOld.Fields(X) & vbCrLf & _
                                    Rs.Fields(X) & vbCrLf & "------" & vbCrLf
                                    
                    Case "CRITICAL_LEVEL1"    'Packing unit
                        If Len(strStr) = 0 Then strStr = strStr & "MANUAL ID." & RsOld!manualid & vbCrLf & _
                                                    "ITEM " & vbCrLf & RsOld!Item_Title & vbCrLf & _
                                            "------" & vbCrLf
                            
                        
                        strStr = strStr & "Promotion" & vbCrLf & _
                                    RsOld.Fields(X) & vbCrLf & _
                                    Rs.Fields(X) & vbCrLf & "------" & vbCrLf
                    
                    Case Else
                        If Len(strStr) = 0 Then strStr = strStr & "MANUAL ID." & RsOld!manualid & vbCrLf & _
                                                    "ITEM " & vbCrLf & RsOld!Item_Title & vbCrLf & _
                                            "------" & vbCrLf
                        
                        strStr = strStr & UCase(Rs.Fields(X).NAME) & vbCrLf & _
                                    RsOld.Fields(X) & vbCrLf & _
                                    Rs.Fields(X) & vbCrLf & _
                                            "------" & vbCrLf
                
                End Select

            End If
        Next
        
        Call SaveLogData("FIN_ITEM", Rs, RsOld, RsOld!Item_ID, RsOld!manualid)
    End If
        Rs.Update
        RsOld.Close
        
    If cItemPrice = True Then
        With Cmd
            .ActiveConnection = Con
            .CommandText = "update fin_item set tnot1 = 0 where manualid = " & txtManualID.Text
            .Execute
        End With
    End If
    '
'    Call Shell(App.Path & "\SyncData.exe", vbMinimizedFocus)
    
    'Call Shell("\\shaheenhp\backup\localfiles\SyncData\SyncData\bin\Debug\" & "SyncData.exe", vbMinimizedFocus)
    
        If Not Len(strStr) = 0 Then
            strStr = strStr & "User :" & cUserName & vbCrLf & _
                        "Machine IP :" & getIP & vbCrLf & _
                        "Date : " & Format(Date, "dd/MMM/yyyy") & vbCrLf & _
                        "Time : " & Time

            Call SendSMSBody(strStr, True)
        End If
     '
     Screen.MousePointer = vbDefault
     If cFoundFlag = False Then
        MsgBox "New Item Inserted .... ", vbInformation, cSelFormId
     Else
        MsgBox "Item Updated .... ", vbInformation, cSelFormId
     End If
   Call clearform
End Sub
Private Sub CmdView_Click()
    Fin_TV.Show vbModal, Me
    TxtID.SetFocus
End Sub

Private Sub Label2_Click()
    TxtID.Text = mLastID
    Fin_OpBal.TxtID.Text = mLastID
End Sub

Private Sub TxtCost_Price_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, True)
''        Dim strvalid As String
''        strvalid = "0123456789."
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtCost_Price))
''            If mLen = 0 Then
''                TxtCost_Price.Text = ""
''            Else
''                TxtCost_Price.Text = Left(Trim(TxtCost_Price), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If

End Sub

Private Sub TxtCountryID_Validate(Cancel As Boolean)
   If Len(Trim(TxtCountryID)) = 0 Or Val(TxtCountryID) = 0 Then
        Exit Sub
   End If
   Screen.MousePointer = vbHourglass
   SQL = "SELECT * FROM Country WHERE Country_id = " & Val(TxtCountryID)
   Set RsDummy = FetchAll(SQL)
   If Not (RsDummy.EOF And RsDummy.BOF) Then
     LblCountryTitle.Caption = "" & RsDummy!country_title
   Else
      Screen.MousePointer = vbDefault
      MsgBox "Country ID not found ... ", vbInformation
      Cancel = True
      RsDummy.Close
      TxtCountryID.SetFocus
      Exit Sub
   End If
   RsDummy.Close
   Screen.MousePointer = vbDefault
End Sub

Private Sub TxtCritical_Level_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, True)
End Sub
Private Sub TxtGLConsID_DblClick()
  cSQLId = "GLGENERAL"
  cSelFormId = "GLCONS_FIN_ITEM"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub TxtGLConsID_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, False)
''        Dim strvalid As String
''        strvalid = "0123456789"
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtGLConsID))
''            If mLen = 0 Then
''                TxtGLConsID.Text = ""
''            Else
''                TxtGLConsID.Text = Left(Trim(TxtGLConsID), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub TxtGLConsID_Validate(Cancel As Boolean)
   If Len(Trim(TxtGLConsID)) = 0 Then
        Exit Sub
   End If
   Screen.MousePointer = vbHourglass
    SQL = "select * from gl0001 where ac_id=" & Val(TxtGLConsID) & " and ac_level = 4"
    Set RsDummy = FetchAll(SQL)
    If Not (RsDummy.EOF And RsDummy.BOF) Then
        TxtGLConsTitle.Caption = "" & RsDummy!ac_title
        If Not IsNull(RsDummy!ed_status) Then
            If RsDummy!ed_status Then
               Screen.MousePointer = vbDefault
               MsgBox "Account ID is Diabled, please re-enter another ... ", vbCritical, cSelFormId
               Cancel = True
               Exit Sub
            End If
        End If
    Else
        Screen.MousePointer = vbDefault
        MsgBox "Account ID not found, please re-enter ... " & Chr(13) & Chr(13) & " Or Main Or Sub Account ID is selected. ", vbInformation, cSelFormId
        Cancel = True
        Exit Sub
    End If
    Screen.MousePointer = vbDefault
End Sub
Private Sub TxtGLDiscID_DblClick()
  cSQLId = "GLGENERAL"
  cSelFormId = "GLDISC_FIN_ITEM"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub TxtGLDiscID_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, False)
''        Dim strvalid As String
''        strvalid = "0123456789"
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtGLDiscID))
''            If mLen = 0 Then
''                TxtGLDiscID.Text = ""
''            Else
''                TxtGLDiscID.Text = Left(Trim(TxtGLDiscID), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub TxtGLDiscID_Validate(Cancel As Boolean)
   If Len(Trim(TxtGLDiscID)) = 0 Then
        Exit Sub
   End If
    Screen.MousePointer = vbHourglass
    SQL = "select * from gl0001 where ac_id=" & Val(TxtGLDiscID) & " and ac_level = 4"
    Set RsDummy = FetchAll(SQL)
    If Not (RsDummy.EOF And RsDummy.BOF) Then
        TxtGLDiscTitle.Caption = "" & RsDummy!ac_title
        If Not IsNull(RsDummy!ed_status) Then
            If RsDummy!ed_status Then
               Screen.MousePointer = vbDefault
               MsgBox "Account ID is Diabled, please re-enter another ... ", vbCritical, cSelFormId
               Cancel = True
               Exit Sub
            End If
        End If
    Else
        Screen.MousePointer = vbDefault
        MsgBox "Account ID not found, please re-enter ... " & Chr(13) & Chr(13) & " Or Main Or Sub Account ID is selected. ", vbInformation, cSelFormId
        Cancel = True
        Exit Sub
    End If
    Screen.MousePointer = vbDefault
End Sub

Private Sub TxtGLPurID_DblClick()
  cSQLId = "GLGENERAL"
  cSelFormId = "GLPUR_FIN_ITEM"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub TxtGLPurID_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, False)
''        Dim strvalid As String
''        strvalid = "0123456789"
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtGLPurID))
''            If mLen = 0 Then
''                TxtGLPurID.Text = ""
''            Else
''                TxtGLPurID.Text = Left(Trim(TxtGLPurID), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub TxtGLPurID_Validate(Cancel As Boolean)
   If Len(Trim(TxtGLPurID)) = 0 Then
        Exit Sub
   End If
    Screen.MousePointer = vbHourglass
    SQL = "select * from gl0001 where ac_id=" & Val(TxtGLPurID) & " and ac_level = 4"
    Set RsDummy = FetchAll(SQL)
    If Not (RsDummy.EOF And RsDummy.BOF) Then
        TxtGLPurTitle.Caption = "" & RsDummy!ac_title
        If Not IsNull(RsDummy!ed_status) Then
            If RsDummy!ed_status Then
               Screen.MousePointer = vbDefault
               MsgBox "Account ID is Diabled, please re-enter another ... ", vbCritical, cSelFormId
               Cancel = True
               Exit Sub
            End If
        End If
    Else
        Screen.MousePointer = vbDefault
        MsgBox "Account ID not found, please re-enter ... " & Chr(13) & Chr(13) & " Or Main Or Sub Account ID is selected. ", vbInformation, cSelFormId
        Cancel = True
        Exit Sub
    End If
    Screen.MousePointer = vbDefault
End Sub

Private Sub TxtGLSalesID_DblClick()
  cSQLId = "GLGENERAL"
  cSelFormId = "GLSALES_FIN_ITEM"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub TxtGLSalesID_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, False)
''        Dim strvalid As String
''        strvalid = "0123456789"
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtGLSalesID))
''            If mLen = 0 Then
''                TxtGLSalesID.Text = ""
''            Else
''                TxtGLSalesID.Text = Left(Trim(TxtGLSalesID), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub
Private Sub TxtGLSalesID_Validate(Cancel As Boolean)
   If Len(Trim(TxtGLSalesID)) = 0 Then
        Exit Sub
   End If
    Screen.MousePointer = vbHourglass
    SQL = "select * from gl0001 where ac_id=" & Val(TxtGLSalesID) & " and ac_level = 4"
    Set RsDummy = FetchAll(SQL)
    If Not (RsDummy.EOF And RsDummy.BOF) Then
        TxtGLSalesTitle.Caption = "" & RsDummy!ac_title
        If Not IsNull(RsDummy!ed_status) Then
            If RsDummy!ed_status Then
               Screen.MousePointer = vbDefault
               MsgBox "Account ID is Diabled, please re-enter another ... ", vbCritical, cSelFormId
               Cancel = True
               Exit Sub
            End If
        End If
    Else
        Screen.MousePointer = vbDefault
        MsgBox "Account ID not found, please re-enter ... " & Chr(13) & Chr(13) & " Or Main Or Sub Account ID is selected. ", vbInformation, cSelFormId
        Cancel = True
        Exit Sub
    End If
    Screen.MousePointer = vbDefault
End Sub

Private Sub TxtGLStaxID_DblClick()
  cSQLId = "GLGENERAL"
  cSelFormId = "GLSTAX_FIN_ITEM"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub TxtGLStaxID_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, False)
''        Dim strvalid As String
''        strvalid = "0123456789"
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtGLStaxID))
''            If mLen = 0 Then
''                TxtGLStaxID.Text = ""
''            Else
''                TxtGLStaxID.Text = Left(Trim(TxtGLStaxID), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub TxtGLStaxID_Validate(Cancel As Boolean)
   If Len(Trim(TxtGLStaxID)) = 0 Then
        Exit Sub
   End If
    Screen.MousePointer = vbHourglass
    SQL = "select * from gl0001 where ac_id=" & Val(TxtGLStaxID) & " and ac_level = 4"
    Set RsDummy = FetchAll(SQL)
    If Not (RsDummy.EOF And RsDummy.BOF) Then
        TxtGLStaxTitle.Caption = "" & RsDummy!ac_title
        If Not IsNull(RsDummy!ed_status) Then
            If RsDummy!ed_status Then
               Screen.MousePointer = vbDefault
               MsgBox "Account ID is Diabled, please re-enter another ... ", vbCritical, cSelFormId
               Cancel = True
               Exit Sub
            End If
        End If
    Else
        Screen.MousePointer = vbDefault
        MsgBox "Account ID not found, please re-enter ... " & Chr(13) & Chr(13) & " Or Main Or Sub Account ID is selected. ", vbInformation, cSelFormId
        Cancel = True
        Exit Sub
    End If
    Screen.MousePointer = vbDefault
End Sub

Private Sub TxtID_DblClick()
  cSQLId = "ITEMID"
  cSelFormId = "ITEMID"
  
  
'  cSQLId = "item MasterInv"
  cSQLId = "ITEMID_MAN_SALE"
  cSelFormId = "ITEMID"
  
  'ITEMID_MAN_SALE
  frmLookUp.Show vbModal, Me
  TxtID_Validate (False)
  
'  TxtID.SetFocus
End Sub
Private Sub CmdClear_Click()
    Call clearform
End Sub
Private Sub cmdClose_Click()
    blnItemActive = False
    Unload Me
End Sub
Private Sub Form_KeyPress(KeyAscii As Integer)
    Call EnterKeyEnable(KeyAscii)
''   If KeyAscii = 13 Then
''      KeyAscii = 0
''      SendKeys "{TAB}"
''   End If
End Sub
Private Sub Form_Load(): Call FormDisplaySetting(Me)
    '
    Call FormDisplaySetting(Me)
'    blnItemActive = False
    SSTab1.Enabled = False
    Caption = cName
    cSelFormId = Line2.Caption
    cSelFormIdExt = "FIN_ITEM"
    TxtID.MaxLength = cFinSeg1 + cFinSeg2 + cFinSeg3 + cFinSeg4
    TxtGLSalesID.MaxLength = cSeg1 + cSeg2 + cSeg3 + cSeg4
    TxtGLConsID.MaxLength = cSeg1 + cSeg2 + cSeg3 + cSeg4
    TxtGLDiscID.MaxLength = cSeg1 + cSeg2 + cSeg3 + cSeg4
    TxtGLStaxID.MaxLength = cSeg1 + cSeg2 + cSeg3 + cSeg4
    CboNature.AddItem "Imported", 0
    CboNature.AddItem "Local", 1
    CboNature.AddItem "Manufactured", 2
    CboNature.ListIndex = 0
    'TxtID.MaxLength = 4
'    TxtTitle.MaxLength = 20
   ' Define Control Mamimum Lengthe
   
    ' Opening Bal
    If Mid(Trim(cUPwordStr), 17, 1) = 0 Then
        cmdOpening.Enabled = False
        ChkEDStatus.Enabled = False
    Else
        cmdOpening.Enabled = True
        ChkEDStatus.Enabled = True
    End If
   'txtAddress.MaxLength = 100
   
   ' Buttone Enable/Disable
   cFoundFlag = False
   'CmdSave.Enabled = False
'   CmdDelete.Enabled = False
   Screen.MousePointer = vbHourglass
   ' Changeable for each Form
   'Change by Maher ali
   'SQL = "SELECT count(customer_id) as cRecTotal, max(customer_id) as cLastid FROM gl0005"
   SQL = "SELECT count(item_id) as cRecTotal, max(item_id) as cLastid FROM v_fin_item"
   '
   Set Rs = FetchAll(SQL)
   If Not (Rs.EOF And Rs.BOF) Then
     ' Assign Values to Text/Controls
     If Not IsNull(Rs!cRecTotal) Then
         TxtRecCount.Caption = str(Rs!cRecTotal)
         cRecTotal = Rs!cRecTotal
     Else
         TxtRecCount.Caption = "0"
         cRecTotal = 0
     End If
     If Not IsNull(Rs!cLastId) Then
         TxtLastID.Caption = str(Rs!cLastId)
     Else
        TxtLastID.Caption = "0"
     End If
    End If
    Rs.Close
    
    'Allow only Admin and utilities
    If Mid(Trim(cUPwordStr), 6, 1) = 1 Then
        cmdOpening.Enabled = True
    Else
        cmdOpening.Enabled = False
    End If
    
    If Not TxtID.Text = "0" Then
        TxtID_Validate (False)
        
    End If
    
    
    Screen.MousePointer = vbDefault
End Sub

Private Sub Txtid_GotFocus()
   LblStatus.Caption = "Ready"
   CmdDelete.Enabled = False
   'CmdSave.Enabled = False
   CmdCategory.Enabled = True
   CmdView.Enabled = True
   cFoundFlag = False
'   SSTab1.Enabled = False

    With TxtID
        .SelStart = 0
        .SelLength = Len(TxtID.Text)
    End With
    
    
    
End Sub
Private Function clearform()
   ' Clear Data Fields
    TxtID.Text = ""
    TxtTitle.Caption = ""
    TxtShortName.Text = ""
    TxtOEM.Text = ""
    txtManualID.Text = "0"
    txtBarcodeID.Text = "0"
    txtWSBarcodeid.Text = "0"
    txtVisaCardRate.Text = "0"
    TxtUOMID.Text = ""
    TxtUomTitle.Caption = ""
    TxtCountryID.Text = ""
    LblCountryTitle.Caption = ""
    '
    TxtMin_Level.Text = ""
    TxtMax_Level.Text = ""
    TxtRO_Qty.Text = ""
    TxtCritical_Level.Text = ""
    '
    'Store Stock Level
    TxtMin_Level1.Text = ""
    TxtMax_Level1.Text = ""
    TxtRO_Qty1.Text = ""
    TxtCritical_Level1.Text = ""
    chkPromotion.Value = 0
    '
    TxtCost_Price.Text = ""
    TxtSales_Price.Text = ""
    txtWSPrice.Text = ""
    TxtSalesPWoGST.Text = "0"
    txtCostWOGST.Text = "0"
    CboNature.ListIndex = 0
    ChkEDStatus.Value = 0
    chkCommission.Value = 0
    TxtGLSalesID.Text = ""
    TxtGLSalesTitle.Caption = ""
    TxtGLPurID.Text = ""
    TxtGLPurTitle.Caption = ""
    TxtGLConsID.Text = ""
    TxtGLConsTitle.Caption = ""
    TxtGLDiscID.Text = ""
    TxtGLDiscTitle.Caption = ""
    TxtGLStaxID.Text = ""
    TxtGLStaxTitle.Caption = ""
    TxtCo.Text = ""
    lblCoTitle.Caption = ""
    TxtOQty.Caption = ""
    TxtCQty.Caption = ""
    TxtOValue.Caption = ""
    TxtCValue.Caption = ""
    TxtRemarks.Text = ""
    TxtSTaxReg.Text = ""
    TxtSTaxUnReg.Text = ""
    TxtAverageCost.Caption = ""
    lblProfitPer.Caption = ""
    TxtMarket_Price.Text = ""
    txtGST.Text = ""
    txtTPRate.Text = ""
    txtSavedCost_price = ""
    'TxtRecCount.Caption = str(cRecTotal)
    ' Define Data Field to be cleared
    grd(0).Clear
    grd(1).Clear
    
   ' Focus
   txtManualID.Enabled = True
   TxtID.Enabled = True
   
   
   
    If chkFocusManBar.Value = 1 Then
        txtBarcodeID.Text = "0"
        txtBarcodeID.SetFocus
    Else
        txtManualID.Text = "0"
        txtManualID.SetFocus
    End If
   
   

'   TxtID.SetFocus
   
End Function

Private Sub TxtID_KeyPress(KeyAscii As Integer)
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
End Sub

Private Sub TxtID_Validate(Cancel As Boolean)
   
On Error GoTo errhandler

'    TxtSales_Price.Text = Rs!sales_Rate
'    'txtTPRate.Text = Rs!oqty1
'
'    TxtSalesPWoGST = CDbl(TxtSales_Price) - CDbl(txtGST)
'
'    txtWSPrice.Text = Rs!disc_p4
'    TxtMarket_Price = Rs!disc_p1
'    txtCostWOGST = Rs!camt1 'Cost Amt with out GST
'
'    TxtCost_Price = CDbl(txtCostWOGST) + CDbl(txtGST)

    grd(0).Clear
    grd(1).Clear
    
   If Len(Trim(TxtID)) = 0 Then
        SSTab1.Enabled = True
        Exit Sub
   Else
        SSTab1.Enabled = True
   End If
   
   
   If Len(Trim(TxtID)) < cFinSeg1 + cFinSeg2 + cFinSeg3 + cFinSeg4 Then
        MsgBox "Invalid : Item ID length ", vbInformation, cSelFormId
        TxtID.SetFocus
        Cancel = True
        Exit Sub
   End If
' ************************************************************
   Screen.MousePointer = vbHourglass
   ' Check if Exist in fin_item Level = 4 act=0=balance sheet
   SQL = "SELECT * FROM fin_cat WHERE item_id = " & Val(TxtID)
   Set RsDummy = FetchAll(SQL)
   Dim mType, mLevel As Integer
   If Not (RsDummy.EOF And RsDummy.BOF) Then
     TxtTitle.Caption = "" & RsDummy!Item_Title
     mLevel = RsDummy!Ac_Level
     If Not IsNull(RsDummy!Ac_Level) Then
          mLevel = RsDummy!Ac_Level
          If mLevel <> 4 Then
                Screen.MousePointer = vbDefault
                MsgBox "Invalid: Use Item ID  ... ", vbInformation
                Cancel = True
                RsDummy.Close
                Exit Sub
          End If
     End If
   Else
       Screen.MousePointer = vbDefault
       MsgBox "Item ID not Found in Finished Category ... ", vbInformation
       Cancel = True
       RsDummy.Close
       Exit Sub
   End If
'   SQL = "SELECT * FROM fin_item WHERE item_id = " & Val(TxtID)
   SQL = "SELECT * FROM v_fin_item WHERE item_id = " & Val(TxtID)
   Set Rs = FetchAll(SQL)
   If Not (Rs.EOF And Rs.BOF) Then
     ' Assign Values to Text/Controls
    'TxtTitle.Text = "" & RS!item_title
    TxtShortName.Text = "" & Rs!item_short
    TxtOEM.Text = "" & Rs!item_oem
    txtManualID = Rs!manualid
    txtBarcodeID = Rs!barcodeid
    txtWSBarcodeid = Rs!barcodeid_ws
    txtVisaCardRate = Rs!visacard_rate
    TxtUOMID.Text = "" & Rs!uom_id
    TxtCountryID.Text = "" & Rs!country_id
    TxtCountryID_Validate False
'    LblCountryTitle.Caption = "" & Rs!country_title
    'TxtUOMTitle.Caption = "" & RS!
    TxtMin_Level.Text = Rs!Min_Level
    TxtMax_Level.Text = Rs!Max_Level
    TxtRO_Qty.Text = Rs!RO_qty 'Change By Kamran
    TxtCost_Price.Text = Format(Rs!cost_Rate, "#########.00")
    txtCostWOGST.Text = Format(Rs!camt1, "#########.00")
    txtGST.Text = Format(Rs!oamt1, "#########.00")
    
    
    
    
'    TxtSalesPWoGST = Format(Rs!oqty1, "#########.00")
    
    TxtCritical_Level.Text = Rs!critical_level
    lblLastPurPer.Caption = "0.00" 'Rs!disc_p1
    '
    'Store Stock Level
    Dim Rss As New ADODB.Recordset
    SQL = "SELECT * FROM fin_item WHERE item_id = " & Val(TxtID)
    Set Rss = FetchAll(SQL)
    If Not (Rss.EOF And Rss.BOF) Then
        txtManualID.Enabled = False
        TxtMin_Level1.Text = Rss!Min_Level1
        TxtMax_Level1.Text = Rss!Max_Level1
        TxtRO_Qty1.Text = Rss!RO_qty1
        'TxtCritical_Level1.Text = Rss!critical_level1
        chkPromotion = Rss!critical_level1
        '
        
'        Temporary Block for FBR Dev
'        TxtSOQty.Caption = Format(Rss("Oqty1"), "#########.00")
'        TxtSCQty.Caption = Format(Rss("cqty1"), "#########.00")
        
    End If
    
    Rss.Close
    '
    TxtSales_Price.Text = Rs!sales_Rate
    txtTPRate.Text = Rs!Cqty1
    
    TxtSalesPWoGST = CDbl(TxtSales_Price) - CDbl(txtGST)
    
    txtWSPrice.Text = Rs!disc_p4
    TxtMarket_Price = Rs!disc_p1
    txtCostWOGST = Rs!camt1 'Cost Amt with out GST
    
    TxtCost_Price = CDbl(txtCostWOGST) + CDbl(txtGST)
    
    txtSavedCost_price.Text = Rs!cost_Rate
    '
    If Not IsNull(Rs!item_nature) Then
        CboNature.ListIndex = Rs!item_nature
    Else
        CboNature.ListIndex = 0
    End If
    TxtUomTitle.Caption = ""
    'Combo1.listText = ""
    ChkEDStatus.Value = Rs!ed_status
    'chkCommission.Value = IIf(RS!commallow = True, 1, 0)
    '
    TxtGLSalesID.Text = Rs!gl_sales_id
    TxtGLPurID.Text = Rs!gl_pur_id
    TxtGLConsID.Text = Rs!gl_cons_id
    TxtGLDiscID.Text = Rs!gl_disc_id
    TxtGLStaxID.Text = Rs!gl_stax_id
    '
    TxtGLSalesTitle.Caption = "" & Rs!gl_sales_title
    TxtGLConsTitle.Caption = "" & Rs!gl_cons_title
    TxtGLDiscTitle.Caption = "" & Rs!gl_disc_title
    TxtGLStaxTitle.Caption = "" & Rs!gl_stax_title
    TxtGLPurTitle.Caption = "" & Rs!gl_pur_title
    '
    TxtUomTitle.Caption = "" & Rs!uom_abbr
    '
    TxtSTaxReg.Text = Rs!STAX_REG
    TxtSTaxUnReg.Text = Rs!STAX_UNREG
    TxtOQty.Caption = Format(Rs("Oqty"), "#########.00")
    TxtCQty.Caption = Format(Rs("cqty"), "#########.00")
    TxtOValue.Caption = Format(Rs("Oamt"), "#########.00")
    TxtCValue.Caption = Format(Rs("camt"), "#########.00")
    
'    If Rs("cqty") <> 0 And Not IsNull(Rs("cqty")) Then
'        TxtAverageCost.Caption = Format(Rs("camt") / Rs("cqty"), "#########.00")
'        If Val(TxtSales_Price) > 0 Then
'            lblProfitPer.Caption = (100 - Int(((Val(TxtAverageCost) / Val(TxtSales_Price)) * 100)))
'        End If
'    Else
'        TxtAverageCost.Caption = "0.00"
'    End If
    
    
    'lblProfitPer.Caption = (100 - Int(((Val(Rs!Cost_Rate) / Val(Rs!sales_Rate)) * 100)))
    If Rs("cost_rate") <> 0 Then
        If Rs!sales_Rate <> 0 Then
            Dim RateDiff As Integer
            RateDiff = Val(Rs!sales_Rate) - Val(Rs!cost_Rate)
            
            Call TxtSalesPWoGST_Validate(False)
            
            'lblProfitPer.Caption = Format((100 - ((Val(Rs!cost_Rate) / Val(Rs!sales_Rate)) * 100)), "########.00")
            'lblProfitPer.Caption = CDbl(Format(((RateDiff * 100) / (Val(Rs!cost_Rate))), "########.00"))
            
            'Org
            'lblProfitPer.Caption = CDbl(Format(((RateDiff / Val(Rs!cost_Rate) * 100)), "########.00"))
            'lblProfitPer.Caption = Format(100 - Format((CDbl(Rs!cost_Rate) / CDbl(Rs!sales_Rate) * 100), "########.00"), "########.00")
            
            'Stop By Kam FOR FBR Collection
'            lblProfitPer.Caption = Format((RateDiff / CDbl(Rs!cost_Rate) * 100), "########.00")
            
'            lblProfitPer.Caption = ((cdbl(Rs!sales_Rate) - CDbl(Rs!cost_Rate) / ) * 100)
        End If
    End If
    
    If Rs("cqty") <> 0 And Not IsNull(Rs("cqty")) Then
    'If Rs("cqty1") <> 0 And Not IsNull(Rs("cqty")) Then
        TxtAverageCost.Caption = Format(Rs("camt") / Rs("cqty"), "#########.00")
        If Val(TxtSales_Price) > 0 Then
'            lblProfitPer.Caption = (100 - Int(((Val(TxtAverageCost) / Val(TxtSales_Price)) * 100)))
        End If
    Else
        TxtAverageCost.Caption = "0.00"
    End If
    
    
'     Check1.Value = RS!TAG_1
'     Check2.Value = RS!TAG_2
     TxtRemarks.Text = "" & Rs!remarks
     ChkEDStatus.Value = Rs!ed_status
     'chkCommission.Value = IIf(RS!commallow = True, 1, 0)
     TxtCo.Text = Rs!co_id
     lblCoTitle.Caption = Rs!co_title
     ' UOM
'        SQL = "SELECT * FROM fin_c002 WHERE uom_id = " & Val(TxtUOMID)
'        Set RsDummy = FETCHALL(SQL)
'        If Not (RsDummy.EOF And RsDummy.BOF) Then
'          TxtUomTitle.Caption = "" & RsDummy!uom_abbr
'        Else
'          TxtUomTitle.Caption = "UOM ID not Found ... "
'        End If
'        RsDummy.Close
     ' Status
     If Len(Trim(TxtShortName.Text)) = 0 Then
        TxtShortName.Text = Left(TxtTitle.Caption, 10)
     End If
     ' GENERAL LEDGER
'     SQL = "select * from gl0001 where ac_id=" & Val(TxtGLSalesID) & " and ac_level = 4"
'     Set RsDummy = FETCHALL(SQL)
'     If Not (RsDummy.EOF And RsDummy.BOF) Then
'         TxtGLSalesTitle.Caption = "" & RsDummy!ac_title
'     Else
'         TxtGLSalesTitle.Caption = "Account ID not found"
'     End If
'     RsDummy.Close
     '
'     SQL = "select * from gl0001 where ac_id=" & Val(TxtGLConsID) & " and ac_level = 4"
'     Set RsDummy = FETCHALL(SQL)
'     If Not (RsDummy.EOF And RsDummy.BOF) Then
'         TxtGLConsTitle.Caption = "" & RsDummy!ac_title
'     Else
'         TxtGLConsTitle.Caption = "Account ID not found"
'     End If
'     RsDummy.Close
     '
'     SQL = "select * from gl0001 where ac_id=" & Val(TxtGLDiscID) & " and ac_level = 4"
'     Set RsDummy = FETCHALL(SQL)
'     If Not (RsDummy.EOF And RsDummy.BOF) Then
'         TxtGLDiscTitle.Caption = "" & RsDummy!ac_title
'     Else
'         TxtGLDiscTitle.Caption = "Account ID not found"
'     End If
'     RsDummy.Close
'     '
'     SQL = "select * from gl0001 where ac_id=" & Val(TxtGLStaxID) & " and ac_level = 4"
'     Set RsDummy = FETCHALL(SQL)
'     If Not (RsDummy.EOF And RsDummy.BOF) Then
'         TxtGLStaxTitle.Caption = "" & RsDummy!ac_title
'     Else
'         TxtGLStaxTitle.Caption = "Account ID not found"
'     End If
'     RsDummy.Close
'     SQL = "select * from gl0001 where ac_id=" & Val(TxtGLPurID) & " and ac_level = 4"
'     Set RsDummy = FETCHALL(SQL)
'     If Not (RsDummy.EOF And RsDummy.BOF) Then
'         TxtGLPurTitle.Caption = "" & RsDummy!ac_title
'     Else
'         TxtGLPurTitle.Caption = "Account ID not found"
'     End If
'     RsDummy.Close
     '''
     CmdDelete.Enabled = True
     CmdSave.Enabled = True
     LblStatus.Caption = "E d i t"
     cFoundFlag = True
   Else
     TxtShortName.Text = Left(TxtTitle.Caption, 10)
     LblStatus.Caption = "N e w"
     cFoundFlag = False
     txtManualID.Enabled = False
   End If
   Screen.MousePointer = vbDefault
' *************************************************************
   
   CmdCategory.Enabled = False
   CmdView.Enabled = False
   TxtID.Enabled = False
   mLastID = TxtID.Text
   
   SSTab1.Enabled = True
    'Call last purchases

    'SQL = "select top " & txtNoOf.Text & " Prod_id,doc_date,QTY,(TOTAL_AMT/QTY),item_id from Fin_Pur_D " & _

    'Purchase Grid
    SQL = "select " & _
            "top " & txtNoOf.Text & " PROD_ID,doc_date,supplier_title, QTY,(TOTAL_AMT/QTY) as rate, Exp_Date " & _
                "from v_fin_pur_exp_date " & _
                    "where ITEM_ID = '" & TxtID.Text & "' " & _
                        "order by doc_date desc"
                        
    Set Rs = FetchAll(SQL)
    If Not (Rs.EOF And Rs.BOF) Then
        grd(0).LoadArray Rs.GetRows()
        With grd(0)
            .TextMatrix(0, 0) = "Pur.#"
            .TextMatrix(0, 1) = "Date"
            .ColWidth(1) = 1200
            .TextMatrix(0, 2) = "Supplier"
            .ColWidth(2) = 3300
            .TextMatrix(0, 3) = "Qty"
            .ColWidth(3) = 1000
            .TextMatrix(0, 4) = "Rate"
            .ColWidth(4) = 1000
            .TextMatrix(0, 5) = "Exp Date"
            .ColWidth(4) = 1000
            
        End With
'        Rs.Close
    End If
    Rs.Close
    
    'Sales Grid
    SQL = "select " & _
            "top " & txtNoOf.Text & " Inv_ID,doc_date,customer_title, QTY,(TOTAL_AMT/QTY) as rate " & _
                "from v_inv1 " & _
                    "where ITEM_ID = '" & TxtID.Text & "' " & _
                        "order by doc_date desc"
                        
    Set Rs = FetchAll(SQL)
    If Not (Rs.EOF And Rs.BOF) Then
        grd(1).LoadArray Rs.GetRows()
    With grd(1)
        .Cols = 5
        .TextMatrix(0, 0) = "Inv.#"
        .TextMatrix(0, 1) = "Date"
        .ColWidth(1) = 1200
        .TextMatrix(0, 2) = "Customer"
        .ColWidth(2) = 3300
        .TextMatrix(0, 3) = "Qty"
        .ColWidth(3) = 1000
        .TextMatrix(0, 4) = "Rate"
        .ColWidth(4) = 1000
    End With

'        Rs.Close
    End If

    Rs.Close
    
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear
    
    
End Sub

Private Sub txtManualID_GotFocus()

    With txtManualID
        .SelStart = 0
        .SelLength = Len(.Text)
    End With
    
End Sub

Private Sub txtManualID_KeyDown(Keycode As Integer, Shift As Integer)
'    cSelFormId = "Stock Balance Date to Date"
'    cFrameStr = "10300110"
'    FrmPrintInvL.Show vbModal, Me
'                .TxtStartCode = TxtID.Text
'                .TxtEndCode = TxtID.Text


On Error GoTo errhandler
    If Keycode = vbKeyF2 Then
        With FrmPrintInvL
            If Not txtManualID.Text = "" Then
                blnAllowFrm = True
                .txtManID.Text = txtManualID.Text
                cSelFormId = "Stock Balance Date to Date"
                cFrameStr = "10300110"
                .Show vbModal, Me
                blnAllowFrm = False
            End If
        End With
    ElseIf Keycode = vbKeyF3 Then
        With FrmSalesTransRpt
            If Not txtManualID.Text = "" Then
                blnAllowFrm = True
                cSelFormId = "Stock Ledger"
                cFrameStr = "10300110"
                .CboReport.ListIndex = 2
                .txtManID.Text = txtManualID.Text
                
'                .TxtStartCode = TxtID.Text
'                .TxtEndCode = TxtID.Text
                .Show vbModal, Me
                blnAllowFrm = False
            End If
        End With
    ElseIf Keycode = vbKeyF4 Then
    'Change by ahsan sb
        TxtID.Text = mLastID
        TxtID.SetFocus
'        Call TxtID_DblClick
        'TxtID_Validate False
    
        'Call LblItem_Click
'        With FrmPurchaseTransRpt
'            .Show vbModal, Me
'        End With
    End If
Exit Sub
errhandler:
    MsgBox Err.Description, vbInformation, cSelFormId
    Err.Clear

End Sub

Private Sub txtManualID_LostFocus()
    If chkBarPrint.Value = 1 Then
         txtNoOf.SetFocus
    End If
End Sub

Private Sub txtManualID_Validate(Cancel As Boolean)
    Dim cSQL As String
    Dim Rs As New ADODB.Recordset

    If TxtID.Text = "0" Then Exit Sub
    
    If txtManualID.Text = "0" Then Exit Sub
    
        cSQL = "SELECT * FROM v_fin_item WHERE manualid = " & Val(txtManualID.Text)
        With Rs
            .Open cSQL, Con, adOpenKeyset, adLockPessimistic
            If Not (.EOF And .BOF) Then
                txtManualID.Enabled = False
                TxtID.Text = !Item_ID
                Call TxtID_Validate(False)
                Exit Sub
            End If
            .Close
        End With
        'Cancel = True
    'Else
    '    MsgBox "ID already exisit."
    '    Cancel = True
    'End If
End Sub

Private Sub TxtMax_Level_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, True)
''        Dim strvalid As String
''        strvalid = "0123456789."
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtMax_Level))
''            If mLen = 0 Then
''                TxtMax_Level.Text = ""
''            Else
''                TxtMax_Level.Text = Left(Trim(TxtMax_Level), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub TxtMin_Level_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, True)
''        Dim strvalid As String
''        strvalid = "0123456789."
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtMin_Level))
''            If mLen = 0 Then
''                TxtMin_Level.Text = ""
''            Else
''                TxtMin_Level.Text = Left(Trim(TxtMin_Level), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub txtNoOf_GotFocus()
    With txtNoOf
        .SelStart = 0
        .SelLength = Len(.Text)
    End With
End Sub

Private Sub txtNoOf_LostFocus()
    If chkBarPrint.Value = 1 Then
         CmdPrnDes.SetFocus
    End If
End Sub


Private Sub TxtRO_Qty_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, True)
''        Dim strvalid As String
''        strvalid = "0123456789."
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtRO_Qty))
''            If mLen = 0 Then
''                TxtRO_Qty.Text = ""
''            Else
''                TxtRO_Qty.Text = Left(Trim(TxtRO_Qty), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub TxtSales_Price_Change()
    cItemPrice = True
End Sub

Private Sub TxtSales_Price_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, True)
End Sub

Private Sub TxtSalesPWoGST_Validate(Cancel As Boolean)

Dim mDifSale_Pur_WOGST As Double


If Val(TxtSalesPWoGST) = 0 Then

    MsgBox "Sale Rate without GST is Zero."
    Exit Sub
    
End If

If Val(txtCostWOGST) = 0 Then
    MsgBox "Purchase Rate without GST is Zero."
    Exit Sub
End If


'If Val(TxtSalesPWoGST) < Val(txtCostWOGST) Then
'      MsgBox "Sales Rate must be Greater then Puchase Rate"
'      Exit Sub
'End If

If Val(TxtSalesPWoGST) > 0 And Val(txtCostWOGST) > 0 Then

    mDifSale_Pur_WOGST = Val(TxtSalesPWoGST) - Val(txtCostWOGST)
    lblProfitPer = Format(mDifSale_Pur_WOGST / Val(TxtSalesPWoGST) * 100, "#########.00")

End If

End Sub


Private Sub txtWSBarcodeid_Change()
Dim cSQL As String
Dim Rs As New ADODB.Recordset

If Not TxtID.Text = "" Then Exit Sub
'If Not txtManualID.Text = "" Or Not txtManualID.Text = "0" Then Exit Sub
If txtWSBarcodeid.Text = "" Or txtWSBarcodeid.Text = "0" Then Exit Sub


cSQL = "SELECT * FROM v_fin_item WHERE barcodeid_ws = '" & Trim(txtWSBarcodeid.Text) & "'"

    Set Rs = FetchAll(cSQL)
    With Rs
        '.Open cSQL, Con, adOpenKeyset, adLockPessimistic
        If Not (.EOF And .BOF) Then
            'MsgBox "Barcode already exisit '" & Rs!Item_ID & "' ," & Rs!Item_Title
            TxtID.Text = !Item_ID
            Call TxtID_Validate(False)
        End If
        .Close
    End With
        
    If chkBarPrint.Value = 1 Then
        txtNoOf.SetFocus
    End If
End Sub

Private Sub txtWSBarcodeid_GotFocus()


With txtWSBarcodeid
    .SelStart = 0
    .SelLength = Len(.Text)
End With

    'txtWSBarcodeid.SelStart = 0
    'txtWSBarcodeid.SelLength = Len(txtWSBarcodeid.Text)
    
    
    If chkBarPrint.Value = 1 Then
        txtNoOf.SetFocus
    End If
End Sub


Private Sub txtWSPrice_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, True)
End Sub
Private Sub TxtUOMID_DblClick()
  cSQLId = "UOMID"
  cSelFormId = "UOM_FIN_ITEM"
  frmLookUp.Show vbModal, Me
End Sub

Private Sub TxtUOMID_KeyPress(KeyAscii As Integer)
    KeyAscii = CheckNumOrChr(KeyAscii, True, False)
''        Dim strvalid As String
''        strvalid = "0123456789"
''        If KeyAscii = 8 Then
''            Dim mLen As Integer
''            mLen = Len(Trim(TxtUOMID))
''            If mLen = 0 Then
''                TxtUOMID.Text = ""
''            Else
''                TxtUOMID.Text = Left(Trim(TxtUOMID), mLen - 1)
''                SendKeys "{END}"
''            End If
''            Exit Sub
''        End If
''        If InStr(strvalid, Chr(KeyAscii)) = 0 Then
''            KeyAscii = 0
''        End If
End Sub

Private Sub TxtUOMID_Validate(Cancel As Boolean)
   If Val(TxtUOMID) = 0 Then
        Exit Sub
   End If
   Screen.MousePointer = vbHourglass
   SQL = "SELECT * FROM fin_c002 WHERE uom_id = " & Val(TxtUOMID)
   Set Rs = FetchAll(SQL)
   If Not (Rs.EOF And Rs.BOF) Then
     ' Assign Values to Text/Controls
     TxtUomTitle.Caption = "" & Rs!uom_abbr
   Else
        TxtUomTitle.Caption = "UOM ID not found ...... "
        Cancel = True
   End If
   Rs.Close
   Screen.MousePointer = vbDefault
End Sub
