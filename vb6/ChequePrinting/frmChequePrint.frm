VERSION 5.00
Begin VB.Form frmChequePrint 
   BorderStyle     =   1  'Fixed Single
   Caption         =   "Print Cheque"
   ClientHeight    =   8460
   ClientLeft      =   45
   ClientTop       =   390
   ClientWidth     =   11880
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   8460
   ScaleWidth      =   11880
   StartUpPosition =   2  'CenterScreen
   Begin VB.ComboBox cboZoom 
      Height          =   315
      Left            =   9840
      Style           =   2  'Dropdown List
      TabIndex        =   14
      Top             =   120
      Width           =   1095
   End
   Begin VB.CheckBox chkGrid 
      Caption         =   "Grid"
      Height          =   255
      Left            =   8880
      TabIndex        =   13
      Top             =   150
      Width           =   735
   End
   Begin VB.PictureBox picPreview 
      AutoRedraw      =   -1  'True
      BackColor       =   &H00FFFFFF&
      Height          =   6375
      Left            =   120
      ScaleHeight     =   6315
      ScaleWidth      =   11595
      TabIndex        =   12
      Top             =   1200
      Width           =   11655
   End
   Begin VB.Frame fraOptions 
      Caption         =   "Print Options"
      Height          =   975
      Left            =   120
      TabIndex        =   3
      Top             =   120
      Width           =   8535
      Begin VB.TextBox txtCopies 
         Height          =   315
         Left            =   7680
         TabIndex        =   11
         Text            =   "1"
         Top             =   360
         Width           =   615
      End
      Begin VB.ComboBox cboPrinter 
         Height          =   315
         Left            =   3600
         Style           =   2  'Dropdown List
         TabIndex        =   9
         Top             =   360
         Width           =   3015
      End
      Begin VB.ComboBox cboPrinterMode 
         Height          =   315
         Left            =   1200
         Style           =   2  'Dropdown List
         TabIndex        =   7
         Top             =   360
         Width           =   1575
      End
      Begin VB.ComboBox cboLayout 
         Height          =   315
         Left            =   1200
         Style           =   2  'Dropdown List
         TabIndex        =   5
         Top             =   0
         Visible         =   0   'False
         Width           =   3015
      End
      Begin VB.Label lblCopies 
         Caption         =   "Copies"
         Height          =   255
         Left            =   6960
         TabIndex        =   10
         Top             =   390
         Width           =   615
      End
      Begin VB.Label lblPrinter 
         Caption         =   "Printer"
         Height          =   255
         Left            =   3000
         TabIndex        =   8
         Top             =   390
         Width           =   615
      End
      Begin VB.Label lblMode 
         Caption         =   "Printer Mode"
         Height          =   255
         Left            =   120
         TabIndex        =   6
         Top             =   390
         Width           =   1095
      End
      Begin VB.Label lblInfo 
         Caption         =   "Payee / Amount / Cheque#"
         Height          =   255
         Left            =   120
         TabIndex        =   4
         Top             =   240
         Width           =   8295
      End
   End
   Begin VB.CommandButton cmdClose 
      Cancel          =   -1  'True
      Caption         =   "&Close"
      Height          =   375
      Left            =   10320
      TabIndex        =   2
      Top             =   7920
      Width           =   1335
   End
   Begin VB.CommandButton cmdPreview 
      Caption         =   "Pre&view"
      Height          =   375
      Left            =   7440
      TabIndex        =   1
      Top             =   7920
      Width           =   1335
   End
   Begin VB.CommandButton cmdPrint 
      Caption         =   "&Print Cheque"
      Default         =   -1  'True
      Height          =   375
      Left            =   8880
      TabIndex        =   0
      Top             =   7920
      Width           =   1335
   End
   Begin VB.Label lblZoom 
      Caption         =   "Zoom"
      Height          =   255
      Left            =   9360
      TabIndex        =   15
      Top             =   150
      Width           =   495
   End
End
Attribute VB_Name = "frmChequePrint"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

' Public entry: set before Show, or call InitFromVoucher
Public gVoucherNo As String
Public gSerialNo As Long
Public gDocTypeID As Long
Public gFiscal As Integer

Private m_Engine As clsChequePrinter
Private m_Zoom As Double
Private m_PanX As Single
Private m_PanY As Single
Private m_Dragging As Boolean
Private m_LastX As Single
Private m_LastY As Single

Public Sub InitFromVoucher(ByVal sVoucherNo As String, Optional ByVal lSerial As Long = 0, _
                           Optional ByVal lDocType As Long = 0, Optional ByVal nFiscal As Integer = 0)
    gVoucherNo = sVoucherNo
    gSerialNo = lSerial
    gDocTypeID = lDocType
    gFiscal = nFiscal
End Sub

Private Sub Form_Load()
    Dim audit As clsChequeAudit
    Set audit = New clsChequeAudit
    If Not audit.HasPermission(CHQ_PERM_PREVIEW) And Not audit.HasPermission(CHQ_PERM_PRINT) Then
        ChqMsgError "You do not have permission to preview/print cheques."
        Unload Me
        Exit Sub
    End If
    
    Set m_Engine = New clsChequePrinter
    m_Zoom = 1#
    m_PanX = 0: m_PanY = 0
    
    cboZoom.Clear
    cboZoom.AddItem "50%": cboZoom.ItemData(cboZoom.NewIndex) = 50
    cboZoom.AddItem "75%": cboZoom.ItemData(cboZoom.NewIndex) = 75
    cboZoom.AddItem "100%": cboZoom.ItemData(cboZoom.NewIndex) = 100
    cboZoom.AddItem "150%": cboZoom.ItemData(cboZoom.NewIndex) = 150
    cboZoom.AddItem "200%": cboZoom.ItemData(cboZoom.NewIndex) = 200
    cboZoom.ListIndex = 2
    
    cboPrinterMode.Clear
    cboPrinterMode.AddItem "Windows Default"
    cboPrinterMode.AddItem "Bank Printer"
    cboPrinterMode.AddItem "Last Used"
    cboPrinterMode.AddItem "Select Printer"
    cboPrinterMode.ListIndex = 2
    
    Call m_Engine.PrinterManager.FillCombo(cboPrinter)
    
    If Len(gVoucherNo) = 0 And gSerialNo = 0 Then
        ChqMsgWarn "No voucher context was supplied."
        Exit Sub
    End If
    
    If Not m_Engine.PrepareFromVoucher(gVoucherNo, gSerialNo, gDocTypeID, gFiscal) Then
        ChqMsgError m_Engine.LastError
        Exit Sub
    End If
    
    Call LoadLayoutsForBank
    Call RefreshInfo
    Call DoPreview
End Sub

Private Sub LoadLayoutsForBank()
    Dim rs As ADODB.Recordset
    Dim sSql As String
    Dim i As Long
    cboLayout.Clear
    sSql = "SELECT LayoutID, LayoutName FROM CHEQUE_LAYOUT_MASTER WHERE BankID=" & m_Engine.ChequeData.BankID & _
           " AND Active=1 ORDER BY IsDefault DESC, LayoutName"
    Set rs = ChqOpenRs(sSql)
    Do While Not rs.EOF
        cboLayout.AddItem NzStr(rs!LayoutName)
        cboLayout.ItemData(cboLayout.NewIndex) = NzLng(rs!LayoutID)
        rs.MoveNext
    Loop
    rs.Close
    For i = 0 To cboLayout.ListCount - 1
        If cboLayout.ItemData(i) = m_Engine.Layout.LayoutID Then
            cboLayout.ListIndex = i
            Exit For
        End If
    Next i
    cboLayout.Visible = True
End Sub

Private Sub RefreshInfo()
    Dim d As clsChequeData
    Set d = m_Engine.ChequeData
    lblInfo.Caption = "Payee: " & d.PayeeName & "   |   Amount: " & Format$(d.Amount, "#,##0.00") & _
                      " " & d.CurrencyCode & "   |   Cheque#: " & d.ChequeNo & _
                      "   |   Voucher: " & d.VoucherNo & "   |   Status: " & d.StatusCode
End Sub

Private Sub DoPreview()
    On Error Resume Next
    picPreview.Cls
    ' Apply pan by shifting ScaleLeft/Top
    picPreview.ScaleLeft = -m_PanX
    picPreview.ScaleTop = -m_PanY
    Call m_Engine.RenderToSurface(picPreview, m_Zoom, (chkGrid.Value = vbChecked))
End Sub

Private Sub cmdPreview_Click()
    Call ApplyPrinterSelection
    Call DoPreview
End Sub

Private Sub cmdPrint_Click()
    Dim bForce As Boolean
    Dim audit As clsChequeAudit
    Set audit = New clsChequeAudit
    
    If Not audit.HasPermission(CHQ_PERM_PRINT) Then
        ChqMsgError "You do not have permission to print cheques."
        Exit Sub
    End If
    
    Call ApplyPrinterSelection
    m_Engine.Copies = Val(txtCopies.Text)
    
    bForce = False
    If m_Engine.ChequeData.AlreadyPrinted Then
        If ChqMsgAsk("This cheque has already been printed." & vbCrLf & vbCrLf & "Reprint?") <> vbYes Then
            Exit Sub
        End If
        If Not audit.HasPermission(CHQ_PERM_REPRINT) Then
            ChqMsgError "You do not have permission to reprint cheques."
            Exit Sub
        End If
        bForce = True
    End If
    
    If m_Engine.PrintCheque(bForce) Then
        ChqMsgInfo "Cheque printed successfully."
        Call RefreshInfo
        Call DoPreview
    Else
        ChqMsgError m_Engine.LastError
    End If
End Sub

Private Sub ApplyPrinterSelection()
    Dim eMode As eChqPrinterMode
    Dim sBankPrn As String
    Dim rs As ADODB.Recordset
    
    eMode = cboPrinterMode.ListIndex + 1
    On Error Resume Next
    Set rs = ChqOpenRs("SELECT DefaultPrinter FROM BANK_MASTER WHERE BankID=" & m_Engine.ChequeData.BankID)
    If Not rs.EOF Then sBankPrn = NzStr(rs!DefaultPrinter)
    If Not rs Is Nothing Then If rs.State = adStateOpen Then rs.Close
    On Error GoTo 0
    
    If eMode = chqPrinterSelect Then
        If cboPrinter.ListIndex >= 0 Then
            m_Engine.PrinterName = cboPrinter.Text
        End If
    Else
        m_Engine.PrinterName = m_Engine.PrinterManager.ResolvePrinter(eMode, sBankPrn, cboPrinter.Text)
        ' Sync combo display
        Dim i As Long
        For i = 0 To cboPrinter.ListCount - 1
            If StrComp(cboPrinter.List(i), m_Engine.PrinterName, vbTextCompare) = 0 Then
                cboPrinter.ListIndex = i
                Exit For
            End If
        Next i
    End If
    Call m_Engine.PrinterManager.SavePreference(CHQ_PREF_PRINTER_MODE, CStr(eMode))
End Sub

Private Sub cboZoom_Click()
    If cboZoom.ListIndex < 0 Then Exit Sub
    m_Zoom = cboZoom.ItemData(cboZoom.ListIndex) / 100#
    Call DoPreview
End Sub

Private Sub cboLayout_Click()
    If cboLayout.ListIndex < 0 Then Exit Sub
    If m_Engine.LoadLayout(cboLayout.ItemData(cboLayout.ListIndex)) Then
        m_Engine.ChequeData.LayoutID = cboLayout.ItemData(cboLayout.ListIndex)
        Call DoPreview
    End If
End Sub

Private Sub chkGrid_Click()
    Call DoPreview
End Sub

Private Sub picPreview_MouseDown(Button As Integer, Shift As Integer, X As Single, Y As Single)
    If Button = vbLeftButton Then
        m_Dragging = True
        m_LastX = X
        m_LastY = Y
    End If
End Sub

Private Sub picPreview_MouseMove(Button As Integer, Shift As Integer, X As Single, Y As Single)
    If m_Dragging Then
        m_PanX = m_PanX + (X - m_LastX)
        m_PanY = m_PanY + (Y - m_LastY)
        m_LastX = X
        m_LastY = Y
        Call DoPreview
    End If
End Sub

Private Sub picPreview_MouseUp(Button As Integer, Shift As Integer, X As Single, Y As Single)
    m_Dragging = False
End Sub

' Mouse wheel zoom — requires subclassing in some VB6 hosts; KeyPreview +/- fallback
Private Sub Form_KeyDown(KeyCode As Integer, Shift As Integer)
    If KeyCode = vbKeyAdd Or KeyCode = 187 Then
        Call ZoomStep(1)
        KeyCode = 0
    ElseIf KeyCode = vbKeySubtract Or KeyCode = 189 Then
        Call ZoomStep(-1)
        KeyCode = 0
    End If
End Sub

Private Sub ZoomStep(ByVal dir As Integer)
    Dim idx As Long
    idx = cboZoom.ListIndex + dir
    If idx < 0 Then idx = 0
    If idx > cboZoom.ListCount - 1 Then idx = cboZoom.ListCount - 1
    cboZoom.ListIndex = idx
End Sub

Private Sub cmdClose_Click()
    Unload Me
End Sub
