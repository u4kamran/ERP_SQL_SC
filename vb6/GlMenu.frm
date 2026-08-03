VERSION 5.00
Object = "{831FDD16-0C5C-11D2-A9FC-0000F8754DA1}#2.1#0"; "MSCOMCTL.OCX"
Begin VB.Form GlMenu 
   BackColor       =   &H00000000&
   Caption         =   "ActiveSoft"
   ClientHeight    =   6510
   ClientLeft      =   165
   ClientTop       =   -1350
   ClientWidth     =   15690
   FillColor       =   &H00E0E0E0&
   LinkTopic       =   "Form2"
   Moveable        =   0   'False
   ScaleHeight     =   6510
   ScaleWidth      =   15690
   StartUpPosition =   2  'CenterScreen
   WindowState     =   2  'Maximized
   Begin VB.PictureBox Picture1 
      BackColor       =   &H00000000&
      BorderStyle     =   0  'None
      Height          =   1500
      Left            =   45
      ScaleHeight     =   1500
      ScaleWidth      =   4005
      TabIndex        =   6
      Top             =   8625
      Visible         =   0   'False
      Width           =   4005
      Begin VB.TextBox Text1 
         Alignment       =   2  'Center
         Appearance      =   0  'Flat
         BackColor       =   &H00000000&
         BorderStyle     =   0  'None
         CausesValidation=   0   'False
         ForeColor       =   &H00C0C0C0&
         Height          =   5715
         Left            =   360
         Locked          =   -1  'True
         MouseIcon       =   "GlMenu.frx":0000
         MousePointer    =   99  'Custom
         MultiLine       =   -1  'True
         TabIndex        =   8
         TabStop         =   0   'False
         Text            =   "GlMenu.frx":030A
         Top             =   -585
         Visible         =   0   'False
         Width           =   3495
      End
      Begin VB.Timer Timer1 
         Interval        =   55
         Left            =   240
         Top             =   3120
      End
      Begin VB.VScrollBar VScroll1 
         Height          =   3615
         Left            =   30
         TabIndex        =   7
         TabStop         =   0   'False
         Top             =   -1770
         Visible         =   0   'False
         Width           =   255
      End
   End
   Begin MSComctlLib.StatusBar StatusBar1 
      Align           =   2  'Align Bottom
      Height          =   405
      Left            =   0
      TabIndex        =   5
      Top             =   6105
      Width           =   15690
      _ExtentX        =   27675
      _ExtentY        =   714
      _Version        =   393216
      BeginProperty Panels {8E3867A5-8586-11D1-B16A-00C0F0283628} 
         NumPanels       =   3
         BeginProperty Panel1 {8E3867AB-8586-11D1-B16A-00C0F0283628} 
            Style           =   6
            TextSave        =   "16/06/2026"
         EndProperty
         BeginProperty Panel2 {8E3867AB-8586-11D1-B16A-00C0F0283628} 
            Style           =   3
            Enabled         =   0   'False
            TextSave        =   "INS"
         EndProperty
         BeginProperty Panel3 {8E3867AB-8586-11D1-B16A-00C0F0283628} 
         EndProperty
      EndProperty
   End
   Begin VB.PictureBox PicFrontPage 
      BackColor       =   &H00E0E0E0&
      BorderStyle     =   0  'None
      Enabled         =   0   'False
      Height          =   3090
      Left            =   -45
      Picture         =   "GlMenu.frx":051C
      ScaleHeight     =   3090
      ScaleWidth      =   3675
      TabIndex        =   3
      Top             =   855
      Width           =   3675
   End
   Begin VB.PictureBox TrayIcon 
      BorderStyle     =   0  'None
      Height          =   495
      Left            =   9375
      Picture         =   "GlMenu.frx":7C8FB
      ScaleHeight     =   495
      ScaleWidth      =   525
      TabIndex        =   2
      Top             =   1425
      Visible         =   0   'False
      Width           =   525
   End
   Begin MSComctlLib.ImageList ImageList1 
      Left            =   10530
      Top             =   1905
      _ExtentX        =   1005
      _ExtentY        =   1005
      BackColor       =   -2147483643
      ImageWidth      =   32
      ImageHeight     =   32
      MaskColor       =   12632256
      _Version        =   393216
      BeginProperty Images {2C247F25-8591-11D1-B16A-00C0F0283628} 
         NumListImages   =   15
         BeginProperty ListImage1 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7CD3D
            Key             =   "KExit"
         EndProperty
         BeginProperty ListImage2 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7D18F
            Key             =   "KAccountID"
         EndProperty
         BeginProperty ListImage3 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7D5E1
            Key             =   "KTranszz"
         EndProperty
         BeginProperty ListImage4 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7DA33
            Key             =   "KReports"
         EndProperty
         BeginProperty ListImage5 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7DE85
            Key             =   "Knotes"
         EndProperty
         BeginProperty ListImage6 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7E2D7
            Key             =   "KBS"
         EndProperty
         BeginProperty ListImage7 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7E729
            Key             =   "KIS"
         EndProperty
         BeginProperty ListImage8 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7EB7B
            Key             =   "KTrans"
         EndProperty
         BeginProperty ListImage9 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7EFCD
            Key             =   "KUtility"
         EndProperty
         BeginProperty ListImage10 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7F41F
            Key             =   "KSecurity"
         EndProperty
         BeginProperty ListImage11 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7F871
            Key             =   "KHelp"
         EndProperty
         BeginProperty ListImage12 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":7FCC3
            Key             =   ""
         EndProperty
         BeginProperty ListImage13 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":80115
            Key             =   ""
         EndProperty
         BeginProperty ListImage14 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":86977
            Key             =   ""
         EndProperty
         BeginProperty ListImage15 {2C247F27-8591-11D1-B16A-00C0F0283628} 
            Picture         =   "GlMenu.frx":8D1D9
            Key             =   ""
         EndProperty
      EndProperty
   End
   Begin MSComctlLib.Toolbar toolbar1 
      Align           =   1  'Align Top
      Height          =   900
      Left            =   0
      TabIndex        =   1
      Top             =   0
      Width           =   15690
      _ExtentX        =   27675
      _ExtentY        =   1588
      ButtonWidth     =   1879
      ButtonHeight    =   1429
      Appearance      =   1
      ImageList       =   "ImageList1"
      _Version        =   393216
      BeginProperty Buttons {66833FE8-8583-11D1-B16A-00C0F0283628} 
         NumButtons      =   13
         BeginProperty Button1 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Exit"
            Key             =   "TBExit"
            Description     =   "Add Account ID"
            Object.ToolTipText     =   "Terminate Financial Accounting Application."
            ImageIndex      =   1
         EndProperty
         BeginProperty Button2 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Account ID"
            Key             =   "TBAcID"
            Object.ToolTipText     =   "Add General Ledger Account ID"
            ImageIndex      =   2
         EndProperty
         BeginProperty Button3 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Trans"
            Key             =   "TBTrans"
            Description     =   "Add/Edit Transactions"
            Object.ToolTipText     =   "Add Edit Delete General Ledger Transactions"
            ImageIndex      =   8
         EndProperty
         BeginProperty Button4 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Reports"
            Key             =   "TBReports"
            Object.ToolTipText     =   "Print/View Trial Balance, GL Listing, Comparative reports."
            ImageIndex      =   4
         EndProperty
         BeginProperty Button5 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Notes"
            Key             =   "TBNotes"
            Object.ToolTipText     =   "Print/View Financial reports like Notes to the Accounts"
            ImageIndex      =   5
         EndProperty
         BeginProperty Button6 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "P && L"
            Key             =   "TBIS"
            Object.ToolTipText     =   "Print/View Income Statement (Profit & Loss Account)"
            ImageIndex      =   7
         EndProperty
         BeginProperty Button7 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "BS"
            Key             =   "TBBS"
            Object.ToolTipText     =   "Print / View Balance Sheet"
            ImageIndex      =   6
         EndProperty
         BeginProperty Button8 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Status"
            Key             =   "TBUtility"
            Object.ToolTipText     =   "Display Current Statistics of The Financial Accounting System."
            ImageIndex      =   9
         EndProperty
         BeginProperty Button9 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Security"
            Key             =   "TBSecurity"
            Object.ToolTipText     =   "Manage User Accounts & User Rights."
            ImageIndex      =   10
         EndProperty
         BeginProperty Button10 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Graph"
            Key             =   "TBGraph"
            Object.ToolTipText     =   "Print / View Graphs (Optional)"
            ImageIndex      =   12
         EndProperty
         BeginProperty Button11 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Help"
            Key             =   "TBHelp"
            Object.ToolTipText     =   "Display Financial Accounting System Help Topics."
            ImageIndex      =   11
         EndProperty
         BeginProperty Button12 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Invoice"
            Key             =   "EnterInvoice"
            Object.ToolTipText     =   "Invoice Transaction Form."
            ImageIndex      =   13
         EndProperty
         BeginProperty Button13 {66833FEA-8583-11D1-B16A-00C0F0283628} 
            Caption         =   "Sales Return"
            Key             =   "salesreturn"
            Description     =   "Sales Return"
            Object.ToolTipText     =   "Sale Return"
            ImageIndex      =   14
         EndProperty
      EndProperty
   End
   Begin VB.Label LblcSoftName 
      BackColor       =   &H00000000&
      Caption         =   "w w w.t e a m l o g i x.c o m"
      BeginProperty Font 
         Name            =   "MS Sans Serif"
         Size            =   12
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H8000000E&
      Height          =   300
      Left            =   7350
      TabIndex        =   4
      Top             =   6900
      Width           =   3285
   End
   Begin VB.Label Label1 
      AutoSize        =   -1  'True
      BackColor       =   &H00000000&
      Caption         =   "TeamLogix"
      BeginProperty Font 
         Name            =   "Times New Roman"
         Size            =   48
         Charset         =   0
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00E0E0E0&
      Height          =   1140
      Left            =   7155
      TabIndex        =   0
      Top             =   6015
      Visible         =   0   'False
      Width           =   4680
   End
   Begin VB.Menu Mnufile 
      Caption         =   "&File"
      Begin VB.Menu MnuFileChangePw 
         Caption         =   "Change Password"
      End
      Begin VB.Menu MnuFilePrinter 
         Caption         =   "Printer Setup"
      End
      Begin VB.Menu MnuBeta 
         Caption         =   "Inventory"
         Begin VB.Menu MnuTest 
            Caption         =   "Production Receipt"
            Visible         =   0   'False
         End
         Begin VB.Menu mnuPr 
            Caption         =   "Purchase Receipt"
            Shortcut        =   {F5}
         End
         Begin VB.Menu MnuPre 
            Caption         =   "Purchase Return"
         End
         Begin VB.Menu MnuPO 
            Caption         =   "Purchase Order"
            Shortcut        =   {F6}
         End
         Begin VB.Menu MnuPI 
            Caption         =   "Stock Adjustment IN"
            Shortcut        =   {F7}
         End
         Begin VB.Menu iBar1 
            Caption         =   "-"
         End
         Begin VB.Menu TestInvoice 
            Caption         =   "Invoice"
            Shortcut        =   ^V
         End
         Begin VB.Menu MnuSalesReturn 
            Caption         =   "Sales Return"
            Shortcut        =   ^R
         End
         Begin VB.Menu MnuStockTrans 
            Caption         =   "Stock Transfer"
            Enabled         =   0   'False
         End
         Begin VB.Menu MnuStockAdjustment 
            Caption         =   "Stock Adjustment Out"
         End
         Begin VB.Menu iBarS 
            Caption         =   "-"
         End
         Begin VB.Menu MnuSPst 
            Caption         =   "Print Stock Transaction"
            Enabled         =   0   'False
            Visible         =   0   'False
            Begin VB.Menu MnuSt 
               Caption         =   "Stock Transaction (Doc #)"
            End
            Begin VB.Menu MnustD1 
               Caption         =   "Stock Transaction (Item + Date)"
            End
            Begin VB.Menu MnuSdw 
               Caption         =   "Stock Date Wise"
            End
         End
         Begin VB.Menu ibar2 
            Caption         =   "-"
            Visible         =   0   'False
         End
         Begin VB.Menu MnuMPst 
            Caption         =   "Print Sales Transactions"
         End
         Begin VB.Menu MnuMPRst 
            Caption         =   "Print Sales Return Transactions"
         End
         Begin VB.Menu MnuPrintInvoice 
            Caption         =   "Print Invoice"
         End
         Begin VB.Menu barmnu1 
            Caption         =   "-"
         End
         Begin VB.Menu MnuPPT 
            Caption         =   "Print Purchase Transactions"
         End
         Begin VB.Menu MnuPPRT 
            Caption         =   "Print Purchase Return Transactions"
         End
         Begin VB.Menu MnuPPIT 
            Caption         =   "Print Purchase (Import) Transactions"
         End
         Begin VB.Menu ibar3 
            Caption         =   "-"
         End
         Begin VB.Menu mnuItemSetup 
            Caption         =   "Item Setup"
            Begin VB.Menu testCategory 
               Caption         =   "Category"
            End
            Begin VB.Menu TestItem 
               Caption         =   "Item"
               Shortcut        =   ^I
            End
            Begin VB.Menu TestUOM 
               Caption         =   "UOM"
            End
            Begin VB.Menu mnuItemCusNo 
               Caption         =   "Customer SMS No"
            End
            Begin VB.Menu mnuItemDataLog 
               Caption         =   "Item Data Log"
               Shortcut        =   ^D
            End
         End
         Begin VB.Menu ibar4 
            Caption         =   "-"
         End
         Begin VB.Menu MnuStockReport 
            Caption         =   "Stock Reports"
            Begin VB.Menu TestStock 
               Caption         =   "Stock Report"
            End
            Begin VB.Menu TestStockCo 
               Caption         =   "Stock Report Co"
            End
            Begin VB.Menu MnuInventoryFGLedger 
               Caption         =   "Stock Ledger"
            End
            Begin VB.Menu MnuInventoryFGD2D 
               Caption         =   "Stock Balance Date to Date"
            End
            Begin VB.Menu mnuItemCusNo1 
               Caption         =   "Customer SMS No"
            End
         End
         Begin VB.Menu ibar5 
            Caption         =   "-"
         End
         Begin VB.Menu mnuStoreStock 
            Caption         =   "Print Store Stock Report"
            Enabled         =   0   'False
         End
         Begin VB.Menu mnuPrnStockTransfer 
            Caption         =   "Print Store Stock Transfer"
            Enabled         =   0   'False
         End
         Begin VB.Menu mnuPrnProfit 
            Caption         =   "Print Profit Statment"
            Enabled         =   0   'False
         End
         Begin VB.Menu ibar99 
            Caption         =   "-"
         End
         Begin VB.Menu Item 
            Caption         =   "Printing of Reports"
            Visible         =   0   'False
         End
         Begin VB.Menu MnuFin_OpBal 
            Caption         =   "Opening Balance"
            Enabled         =   0   'False
         End
         Begin VB.Menu MnuFin_OpBalStore 
            Caption         =   "Opening Balance Store"
            Enabled         =   0   'False
         End
         Begin VB.Menu FinInvGS 
            Caption         =   "General Setup (Sales)"
            Enabled         =   0   'False
         End
         Begin VB.Menu FinInvGP 
            Caption         =   "General Setup (Purchase)"
            Enabled         =   0   'False
         End
         Begin VB.Menu MnuItem_list1 
            Caption         =   "Item List"
         End
         Begin VB.Menu MnuItem_Profit 
            Caption         =   "Profit Statment"
            Enabled         =   0   'False
            Visible         =   0   'False
         End
      End
      Begin VB.Menu FBAR1 
         Caption         =   "-"
      End
      Begin VB.Menu MnuExit 
         Caption         =   "E&xit"
         Shortcut        =   ^X
      End
      Begin VB.Menu utl_invoice 
         Caption         =   "utl invoice"
         Visible         =   0   'False
      End
      Begin VB.Menu utl_purchase 
         Caption         =   "utl purchase"
         Visible         =   0   'False
      End
   End
   Begin VB.Menu MnuID 
      Caption         =   "Account &ID"
      Begin VB.Menu MnuCodingACID 
         Caption         =   "&Account ID"
         Shortcut        =   ^A
      End
      Begin VB.Menu CBAR1 
         Caption         =   "-"
      End
      Begin VB.Menu MnuCodingCustomer 
         Caption         =   "&Customer Info"
      End
      Begin VB.Menu MnuCodingVendor 
         Caption         =   "&Vendor Info"
      End
      Begin VB.Menu CBAR2 
         Caption         =   "-"
      End
      Begin VB.Menu MnuCodingRep 
         Caption         =   "&Rep ID"
      End
      Begin VB.Menu MnuCodingGrpID 
         Caption         =   "&Group ID"
      End
      Begin VB.Menu mnuBankID 
         Caption         =   "Bank ID"
      End
      Begin VB.Menu mnuBankSett 
         Caption         =   "Bank Settlement"
      End
      Begin VB.Menu MnuCodingCoID 
         Caption         =   "Company ID"
      End
      Begin VB.Menu MnuCodingNarID 
         Caption         =   "&Narration ID"
      End
      Begin VB.Menu CBAR3 
         Caption         =   "-"
      End
      Begin VB.Menu MnuCodingCity 
         Caption         =   "Cit&y ID"
      End
      Begin VB.Menu MnuCodingCountry 
         Caption         =   "Coun&try ID"
      End
      Begin VB.Menu cbar4 
         Caption         =   "-"
      End
      Begin VB.Menu MnuReportsCOA 
         Caption         =   "ID Listing"
         Begin VB.Menu MnuListGroupID 
            Caption         =   "Group ID"
         End
         Begin VB.Menu MnuListCityID 
            Caption         =   "City ID"
         End
         Begin VB.Menu MnuListRepID 
            Caption         =   "Representative ID"
         End
         Begin VB.Menu MnuListAitemID 
            Caption         =   "Item ID"
            Shortcut        =   {F12}
         End
         Begin VB.Menu book1 
            Caption         =   "-"
         End
         Begin VB.Menu MnuListCustDir 
            Caption         =   "Customer &Directory"
         End
         Begin VB.Menu MnuListCustDetail 
            Caption         =   "Customer Detail List"
         End
         Begin VB.Menu MnuListVendorDir 
            Caption         =   "Vendor Detail List"
         End
         Begin VB.Menu MnuLstBookID 
            Caption         =   "Book ID"
         End
         Begin VB.Menu book2 
            Caption         =   "-"
         End
         Begin VB.Menu MnuLstView 
            Caption         =   "View"
         End
         Begin VB.Menu Coding1 
            Caption         =   "-"
         End
         Begin VB.Menu MnuLstMainID 
            Caption         =   "Main ID"
         End
         Begin VB.Menu MnuLstSubID 
            Caption         =   "Sub ID"
         End
         Begin VB.Menu MnuLstSubsidiaryID 
            Caption         =   "Subsidiary ID"
         End
         Begin VB.Menu codingb2 
            Caption         =   "-"
         End
         Begin VB.Menu MnuLstMS_ID 
            Caption         =   "Main + Sub ID"
         End
         Begin VB.Menu MnuLstSS_ID 
            Caption         =   "Sub + Subsidiary ID"
         End
         Begin VB.Menu MnuLstMSS_ID 
            Caption         =   "Main + Sub + Subsidiary ID"
         End
      End
   End
   Begin VB.Menu MnuVoucher 
      Caption         =   "&Transaction"
      Begin VB.Menu MnuVoucherEntry 
         Caption         =   "Voucher Entry"
         Shortcut        =   ^J
      End
      Begin VB.Menu mnuCashRecovery 
         Caption         =   "Cash Recovery"
         Visible         =   0   'False
      End
   End
   Begin VB.Menu MnuTransactionListing 
      Caption         =   "Transaction &Listing"
      Begin VB.Menu MnuTransactionListingVNW 
         Caption         =   "&Voucher Transaction (Voucher Wise)"
      End
      Begin VB.Menu MnuTransactionListingDW 
         Caption         =   "Transaction Listing (&Date Wise)"
      End
      Begin VB.Menu VBAR1 
         Caption         =   "-"
      End
      Begin VB.Menu MnuVPrinting 
         Caption         =   "Voucher &Printing"
      End
   End
   Begin VB.Menu MnuReports 
      Caption         =   "&Reports"
      Begin VB.Menu MnuReportsLedger 
         Caption         =   "Account Ledger"
      End
      Begin VB.Menu MnuReportsLedgerGrp 
         Caption         =   "Account Ledger (Grp)"
      End
      Begin VB.Menu RBAR2 
         Caption         =   "-"
      End
      Begin VB.Menu MnuReportsTB 
         Caption         =   "Trial Balance"
         Begin VB.Menu MnuTbMainID 
            Caption         =   "TB Main ID"
         End
         Begin VB.Menu MnuTBSubID 
            Caption         =   "TB Sub ID"
         End
         Begin VB.Menu MnuTBSubsidiary 
            Caption         =   "TB Subsidiary ID"
            Shortcut        =   ^T
         End
         Begin VB.Menu tb1 
            Caption         =   "-"
         End
         Begin VB.Menu MnuTBMS 
            Caption         =   "TB Main + Sub"
         End
         Begin VB.Menu MnuTBSS 
            Caption         =   "TB Sub + Subsidiary"
         End
         Begin VB.Menu MnuTBMSS 
            Caption         =   "TB Main + Sub + Subsidiary"
         End
         Begin VB.Menu tb2a 
            Caption         =   "-"
         End
         Begin VB.Menu MnuTBD2D 
            Caption         =   "TB Date to Date"
         End
         Begin VB.Menu tb2 
            Caption         =   "-"
         End
         Begin VB.Menu MnuTBOB 
            Caption         =   "TB &Opening"
         End
         Begin VB.Menu rptbar3 
            Caption         =   "-"
         End
         Begin VB.Menu MnuTBGroup 
            Caption         =   "TB Group"
         End
         Begin VB.Menu rptbar4 
            Caption         =   "-"
         End
         Begin VB.Menu MnuTBLastYear 
            Caption         =   "TB Last Year"
         End
      End
      Begin VB.Menu MnuReportsTB12 
         Caption         =   "&Comparative Reports"
         Begin VB.Menu MnuReportsComp 
            Caption         =   "Trial Balance &Comparative"
         End
         Begin VB.Menu MnuReportsBudget 
            Caption         =   "Comparison with &Budget"
         End
      End
      Begin VB.Menu tb12 
         Caption         =   "-"
      End
      Begin VB.Menu MnuReportAgingAR 
         Caption         =   "Aging Analysis (A&R)"
      End
      Begin VB.Menu MnuReportAgingAP 
         Caption         =   "Aging Analysis (A&P)"
      End
      Begin VB.Menu tb13 
         Caption         =   "-"
      End
      Begin VB.Menu MnuReportMn 
         Caption         =   "&Management Reports"
         Begin VB.Menu MnuReportsIS 
            Caption         =   "Print &Financial Reports"
         End
         Begin VB.Menu mnuMonitor 
            Caption         =   "Cash Monitor"
            Shortcut        =   {F11}
         End
         Begin VB.Menu mnuSalesDashboard 
            Caption         =   "Sales &Dashboard"
            Shortcut        =   ^D
         End
         Begin VB.Menu TB14 
            Caption         =   "-"
         End
         Begin VB.Menu MnuFR 
            Caption         =   "Create Custom Financial Reports"
            Begin VB.Menu MnuFR_Notes 
               Caption         =   "Notes"
            End
            Begin VB.Menu MnuFR_IS 
               Caption         =   "Income Statement"
            End
            Begin VB.Menu MnuFR_BS 
               Caption         =   "Balance Sheet"
            End
         End
      End
      Begin VB.Menu MnuCust 
         Caption         =   "Customer Detail Aging"
      End
   End
   Begin VB.Menu MnuUtilities 
      Caption         =   "&Utilities"
      Begin VB.Menu MnuUtiltiesCheckBal 
         Caption         =   "&System Statstics"
      End
      Begin VB.Menu UBAR1 
         Caption         =   "-"
      End
      Begin VB.Menu MnuUtiltiesAgingDataAR 
         Caption         =   "Aging Data (Accounts &Receivable)"
      End
      Begin VB.Menu MnuUtiltiesAgingDataAP 
         Caption         =   "Aging Data (Accounts &Payable)"
      End
      Begin VB.Menu UBAR2 
         Caption         =   "-"
      End
      Begin VB.Menu MnuUtiltiesBudgetData 
         Caption         =   "Budget Data (&Monthly)"
      End
      Begin VB.Menu MnuAdmin_2 
         Caption         =   "-"
      End
      Begin VB.Menu MnuAdminOB 
         Caption         =   "&Opening Balance GL"
         Shortcut        =   ^O
      End
      Begin VB.Menu MnuAdminAROB 
         Caption         =   "Opening Balance &AR"
      End
      Begin VB.Menu MnuAdminAPOB 
         Caption         =   "Opening Balance A&P"
      End
      Begin VB.Menu MnuSendSMS 
         Caption         =   "Send SMS to Customer"
      End
      Begin VB.Menu iBar100 
         Caption         =   "-"
      End
      Begin VB.Menu MnuMain 
         Caption         =   "Maintenance"
      End
   End
   Begin VB.Menu MnuAdmin 
      Caption         =   "&Administration"
      Begin VB.Menu MnuAdminUM 
         Caption         =   "&User Manager"
         Shortcut        =   ^U
      End
      Begin VB.Menu MnuAdminPermissions 
         Caption         =   "&Permissions"
         Begin VB.Menu MnuAdminPermissionAc 
            Caption         =   "&Account Permission"
         End
         Begin VB.Menu MnuAdminPermissionBook 
            Caption         =   "&Book Permission"
         End
         Begin VB.Menu MnuAdminPermissionUG 
            Caption         =   "&User Group Permission"
         End
      End
      Begin VB.Menu MnuAdminDefault 
         Caption         =   "&Default Setup"
      End
      Begin VB.Menu MnuAdminVConfirm 
         Caption         =   "Voucher &Signature"
         Shortcut        =   ^C
      End
      Begin VB.Menu mnuQueryEXE 
         Caption         =   "Query Executer"
         Shortcut        =   {F4}
      End
      Begin VB.Menu MnuAdmin_3 
         Caption         =   "-"
      End
      Begin VB.Menu MnuAdminBook 
         Caption         =   " &Book ID"
      End
      Begin VB.Menu MnuAdmin_4 
         Caption         =   "-"
      End
      Begin VB.Menu MnuAdminUserLog 
         Caption         =   "User Data Entry &Log"
         Shortcut        =   ^L
      End
      Begin VB.Menu MnuAdmin_5 
         Caption         =   "-"
      End
      Begin VB.Menu MnuAdminAccountType 
         Caption         =   "Change Account &Type"
      End
      Begin VB.Menu MnuAdmin_6 
         Caption         =   "-"
      End
      Begin VB.Menu MnuAdminReCalc 
         Caption         =   "Re-Calculate Balances"
      End
      Begin VB.Menu BarYearEnd 
         Caption         =   "-"
      End
      Begin VB.Menu MnuAdminYearEnd 
         Caption         =   "&Year End Processing"
      End
      Begin VB.Menu AdminUpdateBalance 
         Caption         =   "-"
      End
      Begin VB.Menu MnuAdminUDLastYear 
         Caption         =   "&Update From Last Year"
      End
   End
   Begin VB.Menu MnuHelp 
      Caption         =   "&Help"
      Begin VB.Menu MnuHelpContents 
         Caption         =   "&Contents"
         HelpContextID   =   11010
      End
      Begin VB.Menu MnuHelpAbout 
         Caption         =   "&About"
      End
   End
End
Attribute VB_Name = "GlMenu"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit
' 31-12-2001
Dim Result As Long
Dim Response As String
Dim TimeToCheck As Integer
Dim ShowAlert As Boolean

Private Sub ddd_Click()
    FrmTestForm.Show vbModal, Me
End Sub

Private Sub FinInvGP_Click()
    Fin_GP.Show vbModal, Me
End Sub

Private Sub FinInvGS_Click()
    Fin_GS.Show vbModal, Me
End Sub

Private Sub Form_Activate()
    If UCase(cLoginName) = "SA" Then
        mnuPrnProfit.Visible = True
        TestInvoice.Visible = True
    Else
        mnuPrnProfit.Visible = False
        TestInvoice.Visible = False
    End If
End Sub

Private Sub Form_Deactivate()
    Timer1.Enabled = False
End Sub

Private Sub Form_KeyDown(Keycode As Integer, Shift As Integer)
Dim Frm1 As Form
Dim Frm2 As Form

    If Keycode = vbKeyF6 Then
'        Set Frm1 = New Fin_InvM
'        Frm1.Show
    ElseIf Keycode = vbKeyF5 Then
        If UCase(cLoginName) = "SA" Then
            FrmTestForm.Show vbModal, Me
        End If
    End If
End Sub


Private Sub MnuAdminAPOB_Click()
    cSelFormId = "AP Aging Opening"
    frmAgingOP.Show vbModal, Me
End Sub

Private Sub MnuAdminAROB_Click()
    cSelFormId = "AR Aging Opening"
    frmAgingOP.Show vbModal, Me
End Sub


Private Sub mnuBankID_Click()
    frmBank.Show vbModal, Me
End Sub

Private Sub mnuBankSett_Click()
    frmBankSet.Show vbModal, Me
End Sub

Private Sub mnuCashRecovery_Click()
    CashRecovery.Show vbModal, Me
End Sub

Private Sub MnuCodingCoID_Click()
    frmCo.Show vbModal, Me
End Sub

Private Sub MnuCust_Click()
cSelcriteria = "SELECT V.AC_ID, c.ac_TITLE,V.DOC_ID,V.DOC_DATE,V.AMT,v.remarks, C.CBAL,C.OBAL " & _
                "From " & _
                "GL0001 C, GL00051 V " & _
                "Where C.AC_ID = V.AC_ID " & _
                "ORDER BY V.AC_ID,V.DOC_ID,V.DOC_DATE"

'cSelcriteria = "SELECT V.AC_ID,T.CUSTOMER_TITLE,V.DOC_ID,V.DOC_DATE,V.AMT,C.CBAL,C.OBAL " & _
'                "From " & _
'                "GL0001 C,GL0005 T,GL00051 V " & _
'                "Where C.AC_ID = T.CUSTOMER_ID And T.CUSTOMER_ID = V.AC_ID " & _
'                "ORDER BY V.AC_ID,V.DOC_ID,V.DOC_DATE"
'cSelcriteria = "SELECT * FROM CUSTTEST"
cReportTitle = "Detailed Opening Aging"

LstInvCust.Show vbModal, Me

End Sub

Private Sub MnuFilePrinter_Click()
    frmDTR.Show vbModal, Me
End Sub

Private Sub MnuFin_OpBalStore_Click()
    Fin_OpBalStore.Show vbModal, Me
End Sub

Private Sub MnuInventoryFGD2D_Click()
    cSelFormId = "Stock Balance Date to Date"
    cFrameStr = "10300110"
    FrmPrintInvL.Show vbModal, Me
End Sub

Private Sub MnuItem_Profit_Click()
    FrmPrintProfit.Show vbModal, Me
End Sub

Private Sub mnuItemCusNo_Click()
    frmCustSMS.Show vbModal, Me
End Sub

Private Sub mnuItemCusNo1_Click()
    frmCustSMS.Show vbModal, Me
End Sub

Private Sub mnuItemDataLog_Click()
    FrmDataLog.Show vbModal, Me
End Sub

Private Sub MnuListCustDetail_Click()
    '
End Sub

Private Sub MnuListVendorDir_Click()
    '
End Sub

Private Sub MnuMain_Click()

Dim Rs, RsItem      As New ADODB.Recordset
Dim Cmd     As New ADODB.Command
Dim cSQL    As String
Dim intcount
Dim dblCostAmt As Double

cSQL = "select * from FIN_INV_d Where DOC_DATE Between '2021/05/01 06:00:00.000' and '2021/05/11 06:00:00.000' where cost_amt = 0 order by inv_id"
Set Rs = FetchAll(cSQL)

    Do While Not Rs.EOF
        cSQL = "select * from fin_item where item_id = '" & Rs!Item_ID
        Set RsItem = FetchAll(cSQL)
        dblCostAmt = RsItem!cost_Rate
        
        Set RsItem = Nothing
    
    
    
        Screen.MousePointer = vbHourglass
        With Cmd
            
            .ActiveConnection = Con
            '.CommandText = "update fin_inv_m set doc_date_t = '" & Rs!doc_date_t - 1 & "'" & _
                            " where serial_no = " & Rs!serial_no
            .CommandText = "update fin_inv_d set cost_amt =  " & dblCostAmt * Rs!Qty & _
                            " where serial_no = " & Rs!serial_no & _
                            " and item_id = " & Rs!Item_ID
                                        
                            
            intcount = intcount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
        End With
        Rs.MoveNext
        Screen.MousePointer = vbNormal
    Loop
    Rs.Close
    
    MsgBox "Maintenance Process is completed ... ", vbOKOnly + vbInformation

Exit Sub




'Mark Values
'cSQL = "SELECT " & _
        "ITEM_ID, manualid, count(item_title) as ac_level1, ITEM_TITLE  " & _
        "From [NSDS1718].[dbo].[Fin_Item]  " & _
        "Where ED_STATUS = 0  " & _
        "group by ITEM_ID, manualid, AC_LEVEL, ITEM_TITLE  " & _
        "order by AC_LEVEL1 desc"
cSQL = "select * from fin_item order by manualid"
  
Set Rs = FetchAll(cSQL)
    intcount = 1

    Do While Not Rs.EOF
        Screen.MousePointer = vbHourglass
        
        Debug.Print intcount & "-MI" & Rs!manualid & "-" & Rs!Item_ID & "-" & Rs!Item_Title
        Rs!mr_cost = intcount
        Rs.Update
        
'        With Cmd
'            MsgBox Rs!Inv_id
'            .ActiveConnection = Con
'            .CommandText = "update fin_item set doc_date_t = doc_date_t -1 " & _
'                            " where serial_no = " & Rs!serial_no
'
'
'            intCount = intCount + 1
'            Debug.Print intCount & " " & .CommandText
'            .Execute
'        End With
        
        
        intcount = intcount + 1
        Rs.MoveNext

    Loop
    Rs.Close




Exit Sub

cSQL = "select * from FIN_INV_m Where DOC_DATE_t Between '2017/05/01 06:00:00.000' and '2017/05/02 06:00:00.000' order by inv_id"
Set Rs = FetchAll(cSQL)
    intcount = 48302

    Do While Not Rs.EOF
        Screen.MousePointer = vbHourglass
        
        
        If Not intcount = Rs!Inv_id Then
            MsgBox intcount & "---" & Rs!Inv_id
            intcount = Rs!Inv_id
        Else
            
        End If
        
        intcount = intcount + 1
        Rs.MoveNext

    Loop
    Rs.Close
    


Exit Sub

cSQL = "select DOC_DATE,DOC_DATE_T - 1,SALE_AMT,serial_no,* from v_Fin_Sale_Disc  where inv_id between 1 AND 99999 " & _
        " and l_uid = 40  " & _
        " and DOC_DATE != DOC_DATE_T " & _
        " And doc_date_t between '2016-3-3 00:00:00.000' And '2016-3-4 00:00:00.000'  " & _
        " order by INV_ID"


Set Rs = FetchAll(cSQL)

    Do While Not Rs.EOF
        Screen.MousePointer = vbHourglass
        With Cmd
            MsgBox Rs!Inv_id
            .ActiveConnection = Con
            '.CommandText = "update fin_inv_m set doc_date_t = '" & Rs!doc_date_t - 1 & "'" & _
                            " where serial_no = " & Rs!serial_no
            .CommandText = "update fin_inv_m set doc_date_t = doc_date_t -1 " & _
                            " where serial_no = " & Rs!serial_no
                                        
                            
            intcount = intcount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
        End With
        Rs.MoveNext
        Screen.MousePointer = vbNormal
    Loop
    Rs.Close
    
    MsgBox "Maintenance Process is completed ... ", vbOKOnly + vbInformation

Exit Sub
'Temp Main

cSQL = "select * from v_Fin_Sale_Disc  where inv_id between 743 AND 743 " & _
        " and l_uid = 40 " & _
        " order by INV_ID"


Set Rs = FetchAll(cSQL)

    Do While Not Rs.EOF
        Screen.MousePointer = vbHourglass
        With Cmd
            MsgBox Rs!Inv_id
            .ActiveConnection = Con
            .CommandText = "update fin_inv_m set doc_date = '" & Rs!doc_date_T & "'" & _
                            " where serial_no = " & Rs!serial_no
                            
            intcount = intcount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
            
            .ActiveConnection = Con
            .CommandText = "update fin_inv_d set doc_date = '" & Rs!doc_date_T & "'" & _
                            " where serial_no = " & Rs!serial_no

            intcount = intcount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
            

            .ActiveConnection = Con
            .CommandText = "update gl0002 set voucher_date = '" & Rs!doc_date_T & "'" & _
                            " where serial_no = " & Rs!serial_no
                            
            intcount = intcount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
            
            .ActiveConnection = Con
            .CommandText = "update gl0003 set vdate = '" & Rs!doc_date_T & "'" & _
                            " where serial_no = " & Rs!serial_no
                            
            intcount = intcount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
            
            
        End With
        Rs.MoveNext
        Screen.MousePointer = vbNormal
    Loop
    Rs.Close
    
    MsgBox "Maintenance Process is completed ... ", vbOKOnly + vbInformation


Exit Sub



'-----------------
'Only Vendor Accounts only
'cSQL = "SELECT * From [NSDS1516].[dbo].[V_FIN_Cbal_LdgBal] " & _
         "  Where CBAL <> OlQty " & _
                " order by AC_ID"
                
'All accounts only


Exit Sub
'Finance Maint
cSQL = "SELECT * From V_FIN_Cbal_LedgerBalAll " & _
         "  Where CBAL <> OlQty " & _
                " order by AC_ID"


Set Rs = FetchAll(cSQL)

    Do While Not Rs.EOF
        Screen.MousePointer = vbHourglass
        With Cmd
            .ActiveConnection = Con
            .CommandText = "update gl0001 set LMBAL = CBAL " & _
                            " where ac_id = " & Rs!ac_id
            intcount = intcount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
            
            .CommandText = "update gl0001 set CBAL = " & Rs!OLQTY & _
                            " where ac_id = " & Rs!ac_id
'            intCount = intCount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
            
            
        End With
        Rs.MoveNext
        Screen.MousePointer = vbNormal
    Loop
    Rs.Close
    
    MsgBox "Maintenance Process is completed ... ", vbOKOnly + vbInformation




Exit Sub


cSQL = " SELECT ITEM_ID, ITEM_TITLE, manualid, barcodeid, BARCODEID_WS, COST_RATE, OQTY, CQTY,(oqty+lqty) as ULqty " & _
         " From v_ficqtylqty " & _
         " where cqty != (oqty+lqty) order by manualid"
         
Set Rs = FetchAll(cSQL)

    Do While Not Rs.EOF
        Screen.MousePointer = vbHourglass
        With Cmd
            .ActiveConnection = Con
            .CommandText = "update fin_item set cqty = " & Rs!ulqty & ", camt =  " & (Rs!ulqty * Rs!cost_Rate) & _
                            " where item_id = " & Rs!Item_ID
            intcount = intcount + 1
            Debug.Print intcount & " " & .CommandText
            .Execute
        End With
        Rs.MoveNext
        Screen.MousePointer = vbNormal
    Loop
    Rs.Close
    
    MsgBox "Maintenance Process is completed ... ", vbOKOnly + vbInformation
    
    
    Exit Sub
    '======================================================
    Call UpdateV2("delete  from FIN_INV_M Where Inv_id = 0")
    Call UpdateV2("delete  from FIN_INV_D Where Inv_id = 0")
    Call UpdateV2("delete from Gl0002 where VOUCHER_ID = 0")
    Call UpdateV2("delete from Gl0003 where VOUCHER_ID = 0")
    Call UpdateV2("delete from fin_ldgr where ITEM_ID = 0 AND QTYDR = 0 AND QTYCR = 0")
       
    
    'Procedure Start
    'Dim Rs As New ADODB.Recordset
    Dim mRs As New ADODB.Recordset
    'Dim cSQL As String
    
    Screen.MousePointer = vbHourglass
    cSQL = "select * from fin_ldgr where amtdr = 0 and amtcr = 0 and doc_type_id = 21 and rate = 0 order by item_id"
            Debug.Print cSQL
    Set Rs = FetchAll(cSQL)
        Do While Not Rs.EOF
            cSQL = "select * from fin_inv_d where item_id = " & Rs!Item_ID & " and serial_no = " & Rs!serial_no
            Debug.Print cSQL
            Set mRs = FetchAll(cSQL)
                cSQL = "update fin_ldgr set rate = " & mRs!Rate & ", amtcr = " & mRs!sale_amt & _
                            " where item_id = " & Rs!Item_ID & " and serial_no = " & Rs!serial_no
                            Debug.Print cSQL
                Call UpdateV(cSQL)
                Set mRs = Nothing
            Rs.MoveNext
        Loop
    Screen.MousePointer = vbNormal
    'Procedure End
    MsgBox "Maintenance Process is completed ... ", vbOKOnly + vbInformation
End Sub

Private Sub mnuMonitor_Click()
    FrmGLTV_IT.Show vbModal, Me
End Sub

Private Sub mnuSalesDashboard_Click()
    FrmSalesDashboard.Show vbModal, Me
End Sub

Private Sub MnuPO_Click()
    Fin_InvM_Order.Show vbModal, Me
End Sub

Private Sub MnuPrintInvoice_Click()
    FrmPrintFin_Invoice.Show vbModal, Me
End Sub

Private Sub mnuPrnProfit_Click()
    FrmPrintProfit.Show vbModal, Me
End Sub

Private Sub mnuPrnStockTransfer_Click()
    FrmStockTransRpt.Show vbModal, Me
End Sub

Private Sub mnuQueryEXE_Click()
    FrmTestForm.Show vbModal, Me
End Sub

Private Sub MnuReportsLedgerGrp_Click()
    
    cSelFormId = "Group General Ledger"
    cFrameStr = "10300103"
    FrmPrintListL.Show vbModal, Me

End Sub

Private Sub MnuSendSMS_Click()
    Fin_SMSTOCUS.Show vbModal, Me
End Sub

Private Sub MnuStockAdjustment_Click()
    Fin_InvM_STA.Show vbModal, Me
End Sub

Private Sub MnuStockTrans_Click()
    Fin_InvM_SI.Show vbModal, Me
End Sub

Private Sub mnuStoreStock_Click()
    FrmPrintFinRpt_StoreStock.Show vbModal
End Sub

Private Sub MnuTBGroup_Click()
    cSelFormId = "TB Group ID"
    cFrameStr = "10100003"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuTBLastYear_Click()
    FrmPrintBalCom.Show vbModal, Me
End Sub

Private Sub MnuTransactionListingDW_Click()
    cSelFormId = "Transaction Listing (DW)"
    cFrameStr = "03"
    frmVPrn.Show vbModal, Me
End Sub

Private Sub MnuUtiltiesAgingDataAP_Click()
    cSelFormId = "Aging Analysis Data (A/P)"
    frmDataAR.Show vbModal, Me
End Sub



Private Sub TestStockCo_Click()
    FrmPrintFinRptCo.Show vbModal
End Sub

Private Sub Timer1_Timer()
'Move the textbox here
If VScroll1.Value >= VScroll1.Min + 30 Then
  VScroll1.Value = VScroll1.Value - 10
Else
  VScroll1.Value = VScroll1.Max
  DoEvents
End If
Text1.Top = VScroll1.Value
DoEvents
End Sub

Private Sub Form_Load(): Call FormDisplaySetting(Me)

    Call StartUp(Me)
    
    'Enable Inventory
    If PIC = 0 Then
        MnuBeta.Enabled = False
    Else
        MnuBeta.Enabled = True
    End If
   

    StatusBar1.Panels(3).Text = cLoginName
    'RichTextBox1.Visible = False ' reminder
    'LblcSoftName.Caption = cSoftName
    ShowProgramInTray
    ' ScrolBar
    VScroll1.Max = Picture1.Height
    VScroll1.Min = 0 - Text1.Height
    VScroll1.Value = VScroll1.Max

    PicFrontPage.Width = Screen.Width
    PicFrontPage.Height = Screen.Height

    ' enable/disable menu
    If SystemMode = 0 Then
        MnuBeta.Enabled = True
    Else
        'MnuBeta.Enabled = False
    End If
    '
    'nYear = Left(Trim(frmLogin.CboYear.Text), 7)
    If SystemMode = 0 Then
        GlMenu.Caption = cName & "  -> Year " & nYear & " Single User :" & nDate
    Else
        GlMenu.Caption = cName & "  -> Year " & nYear & " NetWork :" & nDate
    End If
    ' Add/Edit ID
    If Mid(Trim(cUPwordStr), 1, 1) = 0 Then
            MnuID.Enabled = False
            toolbar1.Buttons(2).Enabled = False
            'Enable Inventory
            MnuBeta.Enabled = False
    End If
    ' Add/Edit/Del Transactions
    If Mid(Trim(cUPwordStr), 2, 1) = 0 Then
            MnuVoucher.Enabled = False
            toolbar1.Buttons(3).Enabled = False
            MnuFilePrinter.Enabled = False
    End If
    'change password
    If Mid(Trim(cUPwordStr), 3, 1) = 0 Then
            MnuFileChangePw.Enabled = False
            MnuFilePrinter.Enabled = True
    End If
    '
    'If Mid(Trim(cUPwordStr), 4, 1) = 0 Then
    '        Mnusetup.Enabled = False
    'End If
    ' adiministration
    If Mid(Trim(cUPwordStr), 5, 1) = 0 Then
            MnuAdmin.Enabled = False
            toolbar1.Buttons(9).Enabled = False
'    ElseIf Mid(Trim(cUPwordStr), 5, 1) = 1 Then
'            MnuAdmin.Enabled = False
'            toolbar1.Buttons(9).Enabled = False
            
    End If
    ' Utilities
    If Mid(Trim(cUPwordStr), 6, 1) = 0 Then
            MnuUtilities.Enabled = False
            toolbar1.Buttons(8).Enabled = False
            MnuFin_OpBal.Enabled = False
            MnuFin_OpBalStore.Enabled = False
            FinInvGS.Enabled = False
            FinInvGP.Enabled = False
'            MnuFilePrinter.Enabled = False
    Else
            MnuFin_OpBal.Enabled = True
            
    
    End If
    
    ' print reports
    If Mid(Trim(cUPwordStr), 7, 1) = 0 Then
            MnuReports.Enabled = False
            toolbar1.Buttons(4).Enabled = False
    End If
    ' print transactions
    If Mid(Trim(cUPwordStr), 8, 1) = 0 Then
            MnuTransactionListing.Enabled = False
    End If
    ' print id listing
    If Mid(Trim(cUPwordStr), 9, 1) = 0 Then
            MnuReportsCOA.Enabled = False
    End If
    ' print MIS reports
    If Mid(Trim(cUPwordStr), 10, 1) = 0 Then
            MnuReportMn.Enabled = False
            toolbar1.Buttons(5).Enabled = False
            toolbar1.Buttons(6).Enabled = False
            toolbar1.Buttons(7).Enabled = False
            'Sales Return
'            toolbar1.Buttons(13).Enabled = False
            FinInvGS.Enabled = False
            FinInvGP.Enabled = False
    Else
            MnuReportMn.Enabled = True
            toolbar1.Buttons(5).Enabled = True
            toolbar1.Buttons(6).Enabled = True
            toolbar1.Buttons(7).Enabled = True
            'Sales Return
'            toolbar1.Buttons(13).Enabled = True
    
            FinInvGS.Enabled = True
            FinInvGP.Enabled = True
            MnuFin_OpBal.Enabled = True
            MnuFin_OpBalStore.Enabled = True
    End If
    
    ' Inventory
    If Mid(Trim(cUPwordStr), 13, 1) = 0 Then
        MnuBeta.Enabled = False
    Else
        MnuBeta.Enabled = True
    End If
    ' Integration
    If Mid(Trim(cUPwordStr), 14, 1) = 0 Then
            FinInvGS.Enabled = False
            FinInvGP.Enabled = False
    Else
            FinInvGS.Enabled = True
            FinInvGP.Enabled = True

    End If
    ' Purchase
    If Mid(Trim(cUPwordStr), 15, 1) = 0 Then
        mnuPr.Enabled = False
        MnuPre.Enabled = False
'        toolbar1.Buttons(13).Enabled = False
    Else
        mnuPr.Enabled = True
        MnuPre.Enabled = True
        toolbar1.Buttons(13).Enabled = True
    End If
    
    ' Sales
    If Mid(Trim(cUPwordStr), 16, 1) = 0 Then
        TestInvoice.Enabled = False
        MnuSalesReturn.Enabled = False
        MnuStockAdjustment.Enabled = False
    Else
        TestInvoice.Enabled = True
        MnuSalesReturn.Enabled = True
        MnuStockAdjustment.Enabled = True
        
    End If
    
    ' Opening Bal
    If Mid(Trim(cUPwordStr), 17, 1) = 0 Then
        MnuFin_OpBal.Enabled = False
        MnuFin_OpBalStore.Enabled = False
    Else
        MnuFin_OpBal.Enabled = True
    End If
    
    ' Print Purchase Transaction
    If Mid(Trim(cUPwordStr), 18, 1) = 0 Then
        MnuPPT.Enabled = False
        MnuPPRT.Enabled = False
        MnuPPIT.Enabled = False
    Else
        MnuPPT.Enabled = True
        MnuPPRT.Enabled = True
        MnuPPIT.Enabled = True
    End If
    
    ' Print Sales Transaction
    If Mid(Trim(cUPwordStr), 19, 1) = 0 Then
        MnuMPst.Enabled = False
        MnuMPRst.Enabled = False
        MnuPrintInvoice.Enabled = False
    Else
        MnuMPst.Enabled = True
        MnuMPRst.Enabled = True
        MnuPrintInvoice.Enabled = True
    End If
    
    ' Stock Reports
    If Mid(Trim(cUPwordStr), 21, 1) = 0 Then
        MnuStockReport.Enabled = False
    Else
        MnuStockReport.Enabled = True
    End If
    
    ' Item Setup
    If Mid(Trim(cUPwordStr), 22, 1) = 0 Then
        mnuItemSetup.Enabled = False
    Else
        mnuItemSetup.Enabled = True
    End If
    
 
End Sub

Private Sub MnuAdminAccountType_Click()
    frmAcType.Show vbModal, Me
End Sub
Private Sub MnuAdminBook_Click()
    frmBook.Show vbModal, Me
End Sub
Private Sub MnuAdminDefault_Click()
    GSETUP.Show vbModal, Me
End Sub
Private Sub MnuAdminOB_Click()
    frmOpBal.Show vbModal, Me
End Sub
Private Sub MnuAdminPermissionBook_Click()
     BookUser.Show vbModal, Me
End Sub
Private Sub MnuAdminReCalc_Click()
    frmRCalc.Show vbModal, Me
End Sub

Private Sub MnuAdminUDLastYear_Click()
    frmUDLY.Show vbModal, Me
End Sub

Private Sub MnuAdminUM_Click()
    frmPword.Show vbModal, Me
End Sub

Private Sub MnuAdminVConfirm_Click()
    Doc_Confirm.Show vbModal, Me
End Sub

Private Sub MnuAdminYearEnd_Click()
   FrmYearEnd.Show vbModal, Me
End Sub

Private Sub MnuCodingACID_Click()
    frmCOA.Show vbModal, Me
End Sub

Private Sub MnuCodingCity_Click()
    frmCity.Show vbModal, Me
End Sub

Private Sub MnuCodingCountry_Click()
    frmCountry.Show vbModal, Me
End Sub

Private Sub MnuCodingCustomer_Click()
    frmCustomer.Show vbModal, Me
End Sub
Private Sub MnuCodingGrpID_Click()
    frmGrpCo.Show vbModal, Me
End Sub

Private Sub MnuCodingNarID_Click()
    Fin_NAR.Show vbModal, Me
End Sub

Private Sub MnuCodingRep_Click()
    frmRep.Show vbModal, Me
End Sub

Private Sub MnuCodingVendor_Click()
    frmVendor.Show vbModal, Me
End Sub

Private Sub MnuExit_Click()
   If MsgBox("This will terminate Application Session. Are you sure?", vbInformation + vbYesNo, cName) = vbYes Then
   
   
        'Alert System Login Start
        strStr = "User :" & cUserName & " has been successfully logout ... " & vbCrLf & _
                "Machine IP :" & getIP & vbCrLf & _
                "Date : " & Format(Date, "dd/MMM/yyyy") & vbCrLf & _
                "Time : " & Time
                
          If AllowSMS = True Then Call SendSMSBody(strStr)
          
        
        
'        Call SendEmail("u4kamran@gmail.com", sEmailPassword, "abuabeera@hotmail.com", "Logout Details ... " & Now, strStr)
        '
        Con.Close
        '

        Result = Shell_NotifyIconA(NIM_DELETE, NI) 'removes the icon from the tray
      End
   End If
End Sub
Private Sub MnuFileChangePw_Click()

    MsgBox MaxNo("fin_inv_no", "inv_id")

    Exit Sub
    ChangePW.Show vbModal, Me
End Sub
Private Sub MnuFin_OpBal_Click()
    Fin_OpBal.Show vbModal, Me
End Sub

Private Sub MnuFR_BS_Click()
    FrmIPBS.Show vbModal, Me
End Sub

Private Sub MnuFR_IS_Click()
    FrmIPIS.Show vbModal, Me
End Sub

Private Sub MnuFR_Notes_Click()
    FrmIPN.Show vbModal, Me
End Sub

Private Sub MnuHelpAbout_Click()
    frmAbout.Show vbModal, Me
End Sub

Private Sub MnuHelpContents_Click()
    TeamM.Show vbModal, Me
End Sub

Private Sub MnuInventoryFGLedger_Click()
    cSelFormId = "Stock Ledger"
    cFrameStr = "10300110"
    FrmPrintInvL.Show vbModal, Me
End Sub

Private Sub MnuItem_list1_Click()
    FrmPrintFinLst.Show vbModal, Me
End Sub

Private Sub MnuListAitemID_Click()
    cSelFormId = "Item ID"
    cFrameStr = "10000004"
    FrmPrintList0.Show vbModal, Me

End Sub

Private Sub MnuListCityID_Click()
    cSelFormId = "City ID"
    cFrameStr = "10000004"
    FrmPrintList0.Show vbModal, Me

End Sub

Private Sub MnuListCustDir_Click()
    cSelFormId = "Customer's Directory"
    cFrameStr = "10000008"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuListGroupID_Click()
    cSelFormId = "Group ID"
    cFrameStr = "10000004"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuListRepID_Click()
    cSelFormId = "Rep ID"
    cFrameStr = "10000004"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuLstBookID_Click()
    cSelFormId = "Book ID"
    cFrameStr = "10000004"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuLstBS_list_Click()
    cSelFormId = "Balance Sheet Title List"
    cFrameStr = "10000003"
    FrmPrintList0.Show vbModal, Me
End Sub


Private Sub MnuLstMainID_Click()
    cSelFormId = "Main ID"
    cFrameStr = "10000008"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuLstMS_ID_Click()
    cSelFormId = "Main + Sub ID"
    cFrameStr = "10000008"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuLstMSS_ID_Click()
    cSelFormId = "Main + Sub + Subsidiary ID"
    cFrameStr = "10000008"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuLstPL_List_Click()
    cSelFormId = "Income Statement Title List"
    cFrameStr = "10000003"
    FrmPrintList0.Show vbModal, Me
End Sub


Private Sub MnuLstSS_ID_Click()
    cSelFormId = "Sub + Subsidiary ID"
    cFrameStr = "10000008"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuLstSubID_Click()
    cSelFormId = "Sub ID"
    cFrameStr = "10000008"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuLstSubsidiaryID_Click()
    cSelFormId = "Subsidiary ID"
    cFrameStr = "10000008"
    FrmPrintList0.Show vbModal, Me
End Sub

Private Sub MnuLstView_Click()
    cSelFormIdExt = ""
    FrmGLTV.Show vbModal, Me
End Sub

Private Sub MnuMPRst_Click()
    FrmSalesRTransRpt.Show vbModal, Me
End Sub

Private Sub MnuMPst_Click()
    FrmSalesTransRpt.Show vbModal, Me
End Sub

Private Sub MnuPI_Click()
   Fin_PurI_M.Show vbModal, Me
End Sub

Private Sub MnuPPIT_Click()
   FrmPurchaseITransRpt.Show vbModal, Me
End Sub

Private Sub MnuPPRT_Click()
    FrmPurchaseRTransRpt.Show vbModal, Me
End Sub

Private Sub MnuPPT_Click()
    FrmPurchaseTransRpt.Show vbModal, Me
End Sub

Private Sub MnuPr_Click()
    Fin_PurM.Show vbModal, Me
End Sub

Private Sub MnuPre_Click()
    Fin_Pur_RM.Show vbModal, Me
End Sub

Private Sub MnuSalesReturn_Click()
    Fin_InvR_M.Show vbModal, Me
End Sub

Private Sub Mnust_Click()
    FrmProductReceiptRpt1.Show vbModal, Me
End Sub

Private Sub MnustD_Click()
    FrmProductReceiptRpt1.Show vbModal, Me
End Sub

Private Sub MnuReportAgingAP_Click()
    cSelFormId = "Print AP Aging Analysis"
    FrmAgingRpt.Show vbModal, Me
End Sub

Private Sub MnuReportAgingAR_Click()
    cSelFormId = "Print AR Aging Analysis"
    FrmAgingRpt.Show vbModal, Me
End Sub
Private Sub MnuReportsBudget_Click()
    FrmPrintListB.Show vbModal, Me
End Sub
Private Sub MnuReportsComp_Click()
  FrmPrintListM.Show vbModal, Me
End Sub
Private Sub MnuReportsIS_Click()
    FrmPrintFR.Show vbModal, Me
End Sub
Private Sub MnuReportsLedger_Click()
    cSelFormId = "General Ledger"
    cFrameStr = "10300108"
    FrmPrintListL.Show vbModal, Me
End Sub

Private Sub MnuSdw_Click()
    FrmProductReceiptRpt2.Show vbModal, Me
End Sub

Private Sub MnuStdw_Click()
    FrmSalesTransRpt.Show vbModal, Me
End Sub

Private Sub MnustD1_Click()
    FrmProductReceiptRpt1.Show vbModal, Me
End Sub

Private Sub MnuTBD2D_Click()
    cSelFormId = "Trial Balance Date to Date"
    cFrameStr = "10300108"
    FrmPrintListL.Show vbModal, Me
End Sub

Private Sub MnuTbMainID_Click()
    cSelFormId = "TB Main ID"
    cFrameStr = "10100008"
    FrmPrintList0.Show vbModal, Me
End Sub
Private Sub MnuTBMS_Click()
    cSelFormId = "TB Main+Sub ID"
    cFrameStr = "10000008"
    FrmPrintList0.Show vbModal, Me
End Sub
Private Sub MnuTBMSS_Click()
    cSelFormId = "TB Main+Sub+Subsidiary ID"
    cFrameStr = "10100008"
    FrmPrintList0.Show vbModal, Me
End Sub
Private Sub MnuTBOB_Click()
    cSelFormId = "TB Opening"
    cFrameStr = "10100008"
    FrmPrintList0.Show vbModal, Me
End Sub
Private Sub MnuTBSS_Click()
    cSelFormId = "TB Sub+Subsidiary ID"
    cFrameStr = "10100008"
    FrmPrintList0.Show vbModal, Me
End Sub
Private Sub MnuTBSubID_Click()
    cSelFormId = "TB Sub ID"
    cFrameStr = "10100008"
    FrmPrintList0.Show vbModal, Me
End Sub
Private Sub MnuTBSubsidiary_Click()
    cSelFormId = "TB Subsidiary ID"
    cFrameStr = "10100008"
    FrmPrintList0.Show vbModal, Me
End Sub
Private Sub MNUTEST_Click()
    Fin_ProdM.Show vbModal, Me
End Sub
Private Sub MnuTransactionListingVNW_Click()
    cSelFormId = "Transaction Listing (VW)"
    cFrameStr = "02"
    frmVPrn.Show vbModal, Me
End Sub
Private Sub MnuUtiltiesAgingDataAR_Click()
    cSelFormId = "Aging Analysis Data (A/R)"
    frmDataAR.Show vbModal, Me
End Sub
Private Sub MnuUtiltiesBudgetData_Click()
  BudgetDataM.Show vbModal, Me
End Sub
Private Sub MnuUtiltiesCheckBal_Click()
    CheckOpBal.Show vbModal, Me
End Sub
Private Sub MnuVoucherEntry_Click()
    VoucherM.Show vbModal, Me
End Sub
Private Sub MnuVoucherQEntry_Click()
    'FrmTmpAdv.Show vbModal, Me
End Sub
Private Sub MnuVPrinting_Click()
    cSelFormId = "Print Voucher"
    cFrameStr = "01"
    frmVPrn.Show vbModal, Me
End Sub
Private Sub testCategory_Click()
    Fin_Cat.Show vbModal, Me
End Sub
'
Private Sub TestInvoice_Click()
Dim Frm As Form

Set Frm = New Fin_InvM
    Frm.Show
    'Fin_InvM.Show 'vbModal, Me
End Sub
Private Sub TestItem_Click()
    Fin_Item.Show vbModal, Me
End Sub

Private Sub testmenu_Click()
    U_Rn_SubID.Show vbModal, Me
End Sub

Private Sub TestStock_Click()
    FrmPrintFinRpt.Show vbModal
End Sub

Private Sub TestUOM_Click()
    Fin_UOM.Show vbModal, Me
End Sub

Private Sub Toolbar1_ButtonClick(ByVal Button As MSComctlLib.Button)
    Select Case Button.Key
'    Select Case Button.Index
'        Case 3
'            MsgBox "button index = 3"
'
'        Case 4
'            MsgBox "button index = 4"
        Case "TBExit"
            If MsgBox("This will terminate Application Session. Are you sure?", vbInformation + vbYesNo, cName) = vbYes Then
                'DB.Close
                With Cmd
                    .ActiveConnection = Con
                    .CommandText = "update contpl set dt_exp = '" & Format(Now, "yyyy-mm-dd hh:mm:ss") & "' WHERE l_id = '" & cLoginName & "'"
                    .Execute
                End With
                Con.Close
                Result = Shell_NotifyIconA(NIM_DELETE, NI) 'removes the icon from the tray
                '
        'Alert System Login Start
                strStr = "User :" & cUserName & " has been successfully logout ... " & vbCrLf & _
                        "Machine IP :" & getIP & vbCrLf & _
                        "Date : " & Format(Date, "dd/MMM/yyyy") & vbCrLf & _
                        "Time : " & Time
                If AllowSMS = True Then Call SendSMSBody(strStr)
                
'                Call SendEmail("u4kamran@gmail.com", sEmailPassword, "abuabeera@hotmail.com", "Logout Details ... " & Now, strStr)
                
                End
            End If

        Case "TBAcID"
            frmCOA.Show vbModal, Me
        Case "TBTrans"
            VoucherM.Show vbModal, Me
        Case "TBReports"
            cSelFormId = "General Ledger"
            cFrameStr = "10300108"
            FrmPrintListL.Show vbModal, Me
        Case "TBNotes"
            FrmIPN.Show vbModal, Me
        Case "TBIS"
            FrmIPIS.Show vbModal, Me
        Case "TBBS"
            FrmIPBS.Show vbModal, Me
        Case "TBUtility"
            CheckOpBal.Show vbModal, Me
        Case "TBSecurity"
            frmPword.Show vbModal, Me
        Case "TBHelp"
            Dim a As Integer
'            a = Shell(App.Path & "\Teamlogix1.exe", vbMinimizedFocus)
        Case "EnterInvoice"
            If UCase(cLoginName) = "SA" Then
                Fin_InvM.Show 'vbModal, Me
            End If
        'Case "PrintInvoice"
        '    FrmPrintFin_Invoice.Show vbModal, Me
        Case "salesreturn"
        If UCase(cLoginName) = "SA" Then
            Fin_InvR_M.Show vbModal, Me
        End If
        Case "TBGraph"
            FrmSalesDashboard.Show vbModal, Me
    End Select
End Sub
Private Sub Form_Unload(Cancel As Integer)
   If MsgBox("This will terminate Application Session. Are you sure?", vbInformation + vbYesNo, cName) = vbYes Then
'      DB.Close
        With Cmd
            .ActiveConnection = Con
            .CommandText = "update contpl set dt_exp = '" & Format(Now, "yyyy-mm-dd hh:mm:ss") & "' WHERE l_id = '" & cLoginName & "'"
            .Execute
        End With
      Result = Shell_NotifyIconA(NIM_DELETE, NI) 'removes the icon from the tray
    'Alert System Login Start
        strStr = "User :" & cUserName & " has been successfully logout ... " & vbCrLf & _
                "Machine IP :" & getIP & vbCrLf & _
                "Date : " & Format(Date, "dd/MMM/yyyy") & vbCrLf & _
                "Time : " & Time
        If AllowSMS = True Then Call SendSMSBody(strStr)
'        Call SendEmail("u4kamran@gmail.com", sEmailPassword, "abuabeera@hotmail.com", "Logout Details ... " & Now, strStr)
      End
   End If
   Cancel = True
End Sub
Private Sub ShowProgramInTray()
    NI.cbSize = Len(NI) 'set the length of this structure
    NI.hwnd = TrayIcon.hwnd 'control to receive messages from
    NI.uID = 0 'uniqueID
    NI.uID = NI.uID + 1
    NI.uFlags = NIF_MESSAGE Or NIF_ICON Or NIF_TIP 'operation flags
    NI.uCallbackMessage = WM_MOUSEMOVE 'recieve messages from mouse activities
    'TrayIcon.Picture = App.Path & "\images\graph07.ico"
    NI.hIcon = TrayIcon.Picture  'the location of the icon to display
    NI.szTip = "TeamLogix: Financial Accounting System " + Chr$(0)  'the tool tip to display
    Result = Shell_NotifyIconA(NIM_ADD, NI) 'add the icon to the system tray
End Sub

Private Sub utl_invoice_Click()
    'UTL_Fin_InvM.Show vbModal, Me
End Sub

Private Sub utl_purchase_Click()
    'UTL_Fin_PurM.Show vbModal, Me
End Sub
