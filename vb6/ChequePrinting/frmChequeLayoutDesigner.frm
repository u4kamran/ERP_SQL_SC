VERSION 5.00
Begin VB.Form frmChequeLayoutDesigner 
   Caption         =   "Cheque Layout Designer"
   ClientHeight    =   9000
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   14000
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form1"
   ScaleHeight     =   9000
   ScaleWidth      =   14000
   StartUpPosition =   2  'CenterScreen
   Begin VB.ListBox lstObjects 
      Height          =   4935
      Left            =   120
      TabIndex        =   12
      Top             =   1200
      Width           =   2415
   End
   Begin VB.PictureBox picCanvas 
      AutoRedraw      =   -1  'True
      BackColor       =   &H00FFFFFF&
      Height          =   6975
      Left            =   2640
      ScaleHeight     =   6915
      ScaleWidth      =   11115
      TabIndex        =   11
      Top             =   1200
      Width           =   11175
   End
   Begin VB.ComboBox cboBank 
      Height          =   315
      Left            =   840
      Style           =   2  'Dropdown List
      TabIndex        =   10
      Top             =   120
      Width           =   2775
   End
   Begin VB.ComboBox cboLayout 
      Height          =   315
      Left            =   4440
      Style           =   2  'Dropdown List
      TabIndex        =   9
      Top             =   120
      Width           =   2775
   End
   Begin VB.ComboBox cboZoom 
      Height          =   315
      Left            =   8040
      Style           =   2  'Dropdown List
      TabIndex        =   8
      Top             =   120
      Width           =   975
   End
   Begin VB.CheckBox chkSnap 
      Caption         =   "Snap"
      Height          =   255
      Left            =   9240
      TabIndex        =   7
      Top             =   150
      Value           =   1  'Checked
      Width           =   735
   End
   Begin VB.CheckBox chkGrid 
      Caption         =   "Grid"
      Height          =   255
      Left            =   10080
      TabIndex        =   6
      Top             =   150
      Value           =   1  'Checked
      Width           =   735
   End
   Begin VB.CommandButton cmdAdd 
      Caption         =   "&Add"
      Height          =   375
      Left            =   120
      TabIndex        =   5
      Top             =   6240
      Width           =   735
   End
   Begin VB.CommandButton cmdDelete 
      Caption         =   "&Del"
      Height          =   375
      Left            =   960
      TabIndex        =   4
      Top             =   6240
      Width           =   735
   End
   Begin VB.CommandButton cmdProps 
      Caption         =   "P&rops"
      Height          =   375
      Left            =   1800
      TabIndex        =   3
      Top             =   6240
      Width           =   735
   End
   Begin VB.CommandButton cmdUndo 
      Caption         =   "Undo"
      Height          =   375
      Left            =   120
      TabIndex        =   2
      Top             =   6720
      Width           =   735
   End
   Begin VB.CommandButton cmdRedo 
      Caption         =   "Redo"
      Height          =   375
      Left            =   960
      TabIndex        =   1
      Top             =   6720
      Width           =   735
   End
   Begin VB.CommandButton cmdSave 
      Caption         =   "&Save"
      Height          =   375
      Left            =   11160
      TabIndex        =   0
      Top             =   8400
      Width           =   1215
   End
   Begin VB.CommandButton cmdTest 
      Caption         =   "Print &Test"
      Height          =   375
      Left            =   9840
      TabIndex        =   16
      Top             =   8400
      Width           =   1215
   End
   Begin VB.CommandButton cmdClose 
      Cancel          =   -1  'True
      Caption         =   "&Close"
      Height          =   375
      Left            =   12480
      TabIndex        =   15
      Top             =   8400
      Width           =   1215
   End
   Begin VB.Label lblBank 
      Caption         =   "Bank"
      Height          =   255
      Left            =   120
      TabIndex        =   14
      Top             =   150
      Width           =   615
   End
   Begin VB.Label lblLayout 
      Caption         =   "Layout"
      Height          =   255
      Left            =   3720
      TabIndex        =   13
      Top             =   150
      Width           =   615
   End
   Begin VB.Label lblStatus 
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Ready"
      Height          =   255
      Left            =   2640
      TabIndex        =   17
      Top             =   8400
      Width           =   6975
   End
   Begin VB.Label lblRuler 
      Caption         =   "Coordinates in millimetres. Drag objects to move. Corner handle to resize."
      Height          =   255
      Left            =   120
      TabIndex        =   18
      Top             =   600
      Width           =   11000
   End
End
Attribute VB_Name = "frmChequeLayoutDesigner"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

' Visual designer: drag / move / resize / snap / undo / redo / zoom
Private m_Layout As clsLayoutManager
Private m_Engine As clsChequePrinter
Private m_Objects() As clsLayoutObject
Private m_Count As Long
Private m_Selected As Long
Private m_Zoom As Double

Private m_Dragging As Boolean
Private m_Resizing As Boolean
Private m_LastMmX As Double
Private m_LastMmY As Double

' Undo/redo stacks (serialized snapshots)
Private m_Undo() As String
Private m_UndoCount As Long
Private m_Redo() As String
Private m_RedoCount As Long

Private Sub Form_Load()
    Dim audit As New clsChequeAudit
    If Not audit.HasPermission(CHQ_PERM_LAYOUT_EDIT) And Not audit.HasPermission(CHQ_PERM_LAYOUT_CREATE) Then
        ChqMsgError "You do not have permission to edit cheque layouts."
        Unload Me
        Exit Sub
    End If
    Set m_Layout = New clsLayoutManager
    Set m_Engine = New clsChequePrinter
    m_Selected = -1
    m_Zoom = 1#
    cboZoom.Clear
    cboZoom.AddItem "50%": cboZoom.ItemData(cboZoom.NewIndex) = 50
    cboZoom.AddItem "75%": cboZoom.ItemData(cboZoom.NewIndex) = 75
    cboZoom.AddItem "100%": cboZoom.ItemData(cboZoom.NewIndex) = 100
    cboZoom.AddItem "150%": cboZoom.ItemData(cboZoom.NewIndex) = 150
    cboZoom.AddItem "200%": cboZoom.ItemData(cboZoom.NewIndex) = 200
    cboZoom.ListIndex = 2
    Call LoadBanks
End Sub

Private Sub LoadBanks()
    Dim rs As ADODB.Recordset
    cboBank.Clear
    Set rs = ChqOpenRs("SELECT BankID, BankName FROM BANK_MASTER WHERE Active=1 ORDER BY BankName")
    Do While Not rs.EOF
        cboBank.AddItem NzStr(rs!BankName)
        cboBank.ItemData(cboBank.NewIndex) = NzLng(rs!BankID)
        rs.MoveNext
    Loop
    rs.Close
    If cboBank.ListCount > 0 Then cboBank.ListIndex = 0
End Sub

Private Sub cboBank_Click()
    Dim rs As ADODB.Recordset
    If cboBank.ListIndex < 0 Then Exit Sub
    cboLayout.Clear
    Set rs = ChqOpenRs("SELECT LayoutID, LayoutName FROM CHEQUE_LAYOUT_MASTER WHERE BankID=" & _
                       cboBank.ItemData(cboBank.ListIndex) & " AND Active=1 ORDER BY LayoutName")
    Do While Not rs.EOF
        cboLayout.AddItem NzStr(rs!LayoutName)
        cboLayout.ItemData(cboLayout.NewIndex) = NzLng(rs!LayoutID)
        rs.MoveNext
    Loop
    rs.Close
    If cboLayout.ListCount > 0 Then cboLayout.ListIndex = 0
End Sub

Private Sub cboLayout_Click()
    If cboLayout.ListIndex < 0 Then Exit Sub
    If Not m_Layout.LoadLayout(cboLayout.ItemData(cboLayout.ListIndex), True) Then
        ChqMsgError "Unable to load layout."
        Exit Sub
    End If
    Call CopyObjectsFromLayout
    Call PushUndo
    Call RefreshList
    Call Redraw
End Sub

Private Sub CopyObjectsFromLayout()
    Dim i As Long
    m_Count = m_Layout.ObjectCount
    If m_Count > 0 Then
        ReDim m_Objects(0 To m_Count - 1)
        For i = 0 To m_Count - 1
            Set m_Objects(i) = m_Layout.LayoutObject(i).CloneMe
        Next i
    Else
        Erase m_Objects
    End If
    m_Selected = -1
End Sub

Private Sub RefreshList()
    Dim i As Long
    lstObjects.Clear
    For i = 0 To m_Count - 1
        lstObjects.AddItem m_Objects(i).ObjectName & " (" & m_Objects(i).ObjectCode & ")"
    Next i
    If m_Selected >= 0 And m_Selected < m_Count Then lstObjects.ListIndex = m_Selected
End Sub

Private Sub Redraw()
    Dim i As Long
    Dim o As clsLayoutObject
    Dim x As Single, y As Single, w As Single, h As Single
    Dim originX As Single, originY As Single
    
    picCanvas.Cls
    picCanvas.ScaleMode = vbTwips
    originX = MmToTwips(10) * m_Zoom
    originY = MmToTwips(10) * m_Zoom
    
    ' Ruler ticks (every 10mm)
    Dim t As Long
    picCanvas.ForeColor = RGB(100, 100, 100)
    For t = 0 To CInt(m_Layout.ChequeWidth) Step 10
        x = originX + MmToTwips(t) * m_Zoom
        picCanvas.Line (x, originY - MmToTwips(3) * m_Zoom)-(x, originY)
        picCanvas.CurrentX = x - 50
        picCanvas.CurrentY = originY - MmToTwips(6) * m_Zoom
        picCanvas.FontSize = 6
        picCanvas.Print CStr(t)
    Next t
    
    ' Cheque boundary
    picCanvas.Line (originX, originY)- _
        (originX + MmToTwips(m_Layout.ChequeWidth) * m_Zoom, originY + MmToTwips(m_Layout.ChequeHeight) * m_Zoom), _
        RGB(0, 0, 0), B
    
    If chkGrid.Value = vbChecked Then
        Dim gx As Single, gy As Single, stepTw As Single
        stepTw = MmToTwips(5) * m_Zoom
        picCanvas.DrawStyle = vbDot
        gx = originX
        Do While gx <= originX + MmToTwips(m_Layout.ChequeWidth) * m_Zoom
            picCanvas.Line (gx, originY)-(gx, originY + MmToTwips(m_Layout.ChequeHeight) * m_Zoom), RGB(230, 230, 230)
            gx = gx + stepTw
        Loop
        gy = originY
        Do While gy <= originY + MmToTwips(m_Layout.ChequeHeight) * m_Zoom
            picCanvas.Line (originX, gy)-(originX + MmToTwips(m_Layout.ChequeWidth) * m_Zoom, gy), RGB(230, 230, 230)
            gy = gy + stepTw
        Loop
        picCanvas.DrawStyle = vbSolid
    End If
    
    For i = 0 To m_Count - 1
        Set o = m_Objects(i)
        If o.Visible Then
            x = originX + MmToTwips(o.XPos) * m_Zoom
            y = originY + MmToTwips(o.YPos) * m_Zoom
            w = MmToTwips(o.Width) * m_Zoom
            h = MmToTwips(o.Height) * m_Zoom
            If i = m_Selected Then
                picCanvas.Line (x, y)-(x + w, y + h), RGB(0, 120, 215), B
                ' resize handle
                picCanvas.Line (x + w - 80, y + h - 80)-(x + w, y + h), RGB(0, 120, 215), BF
            Else
                picCanvas.Line (x, y)-(x + w, y + h), RGB(160, 160, 160), B
            End If
            picCanvas.FontName = o.FontName
            picCanvas.FontSize = o.FontSize * m_Zoom
            picCanvas.FontBold = o.Bold
            picCanvas.CurrentX = x + 30
            picCanvas.CurrentY = y + 30
            picCanvas.ForeColor = vbBlack
            picCanvas.Print o.ObjectName
        End If
    Next i
    
    If m_Selected >= 0 Then
        Set o = m_Objects(m_Selected)
        lblStatus.Caption = o.ObjectName & "  X=" & Format$(o.XPos, "0.000") & " Y=" & Format$(o.YPos, "0.000") & _
                            " W=" & Format$(o.Width, "0.000") & " H=" & Format$(o.Height, "0.000") & " mm"
    End If
End Sub

Private Function HitTest(ByVal X As Single, ByVal Y As Single, ByRef bOnHandle As Boolean) As Long
    Dim i As Long
    Dim o As clsLayoutObject
    Dim ox As Single, oy As Single, ow As Single, oh As Single
    Dim originX As Single, originY As Single
    originX = MmToTwips(10) * m_Zoom
    originY = MmToTwips(10) * m_Zoom
    bOnHandle = False
    HitTest = -1
    For i = m_Count - 1 To 0 Step -1
        Set o = m_Objects(i)
        ox = originX + MmToTwips(o.XPos) * m_Zoom
        oy = originY + MmToTwips(o.YPos) * m_Zoom
        ow = MmToTwips(o.Width) * m_Zoom
        oh = MmToTwips(o.Height) * m_Zoom
        If X >= ox And X <= ox + ow And Y >= oy And Y <= oy + oh Then
            HitTest = i
            If X >= ox + ow - 100 And Y >= oy + oh - 100 Then bOnHandle = True
            Exit Function
        End If
    Next i
End Function

Private Sub picCanvas_MouseDown(Button As Integer, Shift As Integer, X As Single, Y As Single)
    Dim bHandle As Boolean
    Dim idx As Long
    idx = HitTest(X, Y, bHandle)
    m_Selected = idx
    Call RefreshList
    Call Redraw
    If idx < 0 Then Exit Sub
    m_LastMmX = TwipsToMm(X / m_Zoom)
    m_LastMmY = TwipsToMm(Y / m_Zoom)
    m_Resizing = bHandle
    m_Dragging = Not bHandle
    Call PushUndo
End Sub

Private Sub picCanvas_MouseMove(Button As Integer, Shift As Integer, X As Single, Y As Single)
    Dim dx As Double, dy As Double
    Dim curX As Double, curY As Double
    If m_Selected < 0 Then Exit Sub
    If Not (m_Dragging Or m_Resizing) Then Exit Sub
    If Button <> vbLeftButton Then Exit Sub
    
    curX = TwipsToMm(X / m_Zoom)
    curY = TwipsToMm(Y / m_Zoom)
    dx = curX - m_LastMmX
    dy = curY - m_LastMmY
    m_LastMmX = curX
    m_LastMmY = curY
    
    With m_Objects(m_Selected)
        If m_Dragging Then
            .XPos = .XPos + dx
            .YPos = .YPos + dy
            If chkSnap.Value = vbChecked Then
                .XPos = SnapToGridMm(.XPos)
                .YPos = SnapToGridMm(.YPos)
            End If
        ElseIf m_Resizing Then
            .Width = .Width + dx
            .Height = .Height + dy
            If .Width < 2 Then .Width = 2
            If .Height < 2 Then .Height = 2
            If chkSnap.Value = vbChecked Then
                .Width = SnapToGridMm(.Width)
                .Height = SnapToGridMm(.Height)
            End If
        End If
    End With
    Call Redraw
End Sub

Private Sub picCanvas_MouseUp(Button As Integer, Shift As Integer, X As Single, Y As Single)
    m_Dragging = False
    m_Resizing = False
End Sub

Private Sub lstObjects_Click()
    m_Selected = lstObjects.ListIndex
    Call Redraw
End Sub

Private Sub cmdAdd_Click()
    Dim audit As New clsChequeAudit
    Dim o As New clsLayoutObject
    Dim sCode As String
    If Not audit.HasPermission(CHQ_PERM_LAYOUT_EDIT) Then
        ChqMsgError "No permission."
        Exit Sub
    End If
    sCode = InputBox("Object code (PAYEE_NAME, AMOUNT, AMOUNT_WORDS, CHEQUE_DATE, AC_PAYEE, CUSTOM_TEXT, ...):", "Add Object", "CUSTOM_TEXT")
    If Len(Trim$(sCode)) = 0 Then Exit Sub
    Call PushUndo
    o.LayoutID = m_Layout.LayoutID
    o.ObjectCode = UCase$(Trim$(sCode))
    o.ObjectName = o.ObjectCode
    o.XPos = 20: o.YPos = 20: o.Width = 40: o.Height = 6
    o.FontName = "Arial": o.FontSize = 10
    o.Visible = True: o.PrintOrder = (m_Count + 1) * 10
    o.MinFontSize = 7
    If o.ObjectCode = CHQ_OBJ_AC_PAYEE Then o.DefaultText = "A/C PAYEE"
    If o.ObjectCode = CHQ_OBJ_CUSTOM_TEXT Then o.DefaultText = "Text"
    ReDim Preserve m_Objects(0 To m_Count)
    Set m_Objects(m_Count) = o
    m_Selected = m_Count
    m_Count = m_Count + 1
    Call RefreshList
    Call Redraw
End Sub

Private Sub cmdDelete_Click()
    Dim audit As New clsChequeAudit
    Dim i As Long
    If m_Selected < 0 Then Exit Sub
    If Not audit.HasPermission(CHQ_PERM_LAYOUT_EDIT) Then Exit Sub
    If ChqMsgAsk("Delete object '" & m_Objects(m_Selected).ObjectName & "'?") <> vbYes Then Exit Sub
    Call PushUndo
    If m_Objects(m_Selected).DetailID > 0 Then
        Call m_Layout.DeleteObject(m_Objects(m_Selected).DetailID, m_Layout.LayoutID)
    End If
    For i = m_Selected To m_Count - 2
        Set m_Objects(i) = m_Objects(i + 1)
    Next i
    m_Count = m_Count - 1
    If m_Count > 0 Then
        ReDim Preserve m_Objects(0 To m_Count - 1)
    Else
        Erase m_Objects
    End If
    m_Selected = -1
    Call RefreshList
    Call Redraw
End Sub

Private Sub cmdProps_Click()
    Dim o As clsLayoutObject
    Dim s As String
    If m_Selected < 0 Then Exit Sub
    Set o = m_Objects(m_Selected)
    Call PushUndo
    s = InputBox("Object Name:", "Properties", o.ObjectName)
    If Len(s) > 0 Then o.ObjectName = s
    s = InputBox("Font Name:", "Properties", o.FontName)
    If Len(s) > 0 Then o.FontName = s
    s = InputBox("Font Size:", "Properties", CStr(o.FontSize))
    If IsNumeric(s) Then o.FontSize = CDbl(s)
    s = InputBox("Bold (0/1):", "Properties", IIf(o.Bold, "1", "0"))
    If s = "1" Then o.Bold = True Else o.Bold = False
    s = InputBox("Alignment 0=Left 1=Center 2=Right:", "Properties", CStr(o.Alignment))
    If IsNumeric(s) Then o.Alignment = CInt(s)
    s = InputBox("Rotation degrees:", "Properties", CStr(o.Rotation))
    If IsNumeric(s) Then o.Rotation = CInt(s)
    s = InputBox("Visible (0/1):", "Properties", IIf(o.Visible, "1", "0"))
    If s = "1" Then o.Visible = True Else o.Visible = False
    s = InputBox("Default Text (for CUSTOM_TEXT / AC_PAYEE):", "Properties", o.DefaultText)
    o.DefaultText = s
    s = InputBox("Print Order:", "Properties", CStr(o.PrintOrder))
    If IsNumeric(s) Then o.PrintOrder = CLng(s)
    Call RefreshList
    Call Redraw
End Sub

Private Sub cmdSave_Click()
    Dim i As Long
    Dim audit As New clsChequeAudit
    If Not audit.HasPermission(CHQ_PERM_LAYOUT_EDIT) Then
        ChqMsgError "No permission to save layouts."
        Exit Sub
    End If
    For i = 0 To m_Count - 1
        m_Objects(i).LayoutID = m_Layout.LayoutID
        If Not m_Layout.SaveObject(m_Objects(i)) Then
            ChqMsgError "Failed saving object " & m_Objects(i).ObjectName
            Exit Sub
        End If
    Next i
    Call m_Layout.LoadLayout(m_Layout.LayoutID, True)
    Call CopyObjectsFromLayout
    Call RefreshList
    Call Redraw
    ChqMsgInfo "Layout saved. New bank cheques can use this layout with no program changes."
End Sub

Private Sub cmdTest_Click()
    Set m_Engine.ChequeData = New clsChequeData
    With m_Engine.ChequeData
        .PayeeName = "SAMPLE PAYEE NAME"
        .Amount = 1250
        .CurrencyCode = "PKR"
        .ChequeDate = Date
        .VoucherNo = "TEST"
        .ChequeNo = "000001"
        .CompanyName = "TEST COMPANY"
        .Narration = "Alignment test"
        .StatusCode = CHQ_STATUS_DRAFT
    End With
    Call m_Engine.LoadLayout(m_Layout.LayoutID)
    m_Engine.PrinterName = WindowsDefaultPrinterName()
    If m_Engine.PrintTestPage() Then
        ChqMsgInfo "Test page sent to printer."
    Else
        ChqMsgError m_Engine.LastError
    End If
End Sub

Private Sub Snapshot(ByRef sOut As String)
    Dim i As Long
    Dim s As String
    s = ""
    For i = 0 To m_Count - 1
        With m_Objects(i)
            s = s & .DetailID & "|" & .ObjectName & "|" & .ObjectCode & "|" & .XPos & "|" & .YPos & "|" & _
                .Width & "|" & .Height & "|" & .FontName & "|" & .FontSize & "|" & IIf(.Bold, 1, 0) & "|" & _
                IIf(.Italic, 1, 0) & "|" & .Alignment & "|" & IIf(.Visible, 1, 0) & "|" & .Rotation & "|" & _
                .PrintOrder & "|" & Replace$(.DefaultText, "|", "/") & "|" & .MinFontSize & vbCrLf
        End With
    Next i
    sOut = s
End Sub

Private Sub RestoreSnapshot(ByVal sData As String)
    Dim lines() As String
    Dim parts() As String
    Dim i As Long
    Dim o As clsLayoutObject
    lines = Split(sData, vbCrLf)
    m_Count = 0
    Erase m_Objects
    For i = LBound(lines) To UBound(lines)
        If Len(Trim$(lines(i))) = 0 Then GoTo NextLine
        parts = Split(lines(i), "|")
        If UBound(parts) < 16 Then GoTo NextLine
        Set o = New clsLayoutObject
        o.DetailID = CLng(Val(parts(0)))
        o.ObjectName = parts(1)
        o.ObjectCode = parts(2)
        o.XPos = CDbl(Val(parts(3)))
        o.YPos = CDbl(Val(parts(4)))
        o.Width = CDbl(Val(parts(5)))
        o.Height = CDbl(Val(parts(6)))
        o.FontName = parts(7)
        o.FontSize = CDbl(Val(parts(8)))
        o.Bold = (parts(9) = "1")
        o.Italic = (parts(10) = "1")
        o.Alignment = CInt(Val(parts(11)))
        o.Visible = (parts(12) = "1")
        o.Rotation = CInt(Val(parts(13)))
        o.PrintOrder = CLng(Val(parts(14)))
        o.DefaultText = parts(15)
        o.MinFontSize = CDbl(Val(parts(16)))
        o.LayoutID = m_Layout.LayoutID
        ReDim Preserve m_Objects(0 To m_Count)
        Set m_Objects(m_Count) = o
        m_Count = m_Count + 1
NextLine:
    Next i
    m_Selected = -1
    Call RefreshList
    Call Redraw
End Sub

Private Sub PushUndo()
    Dim s As String
    Call Snapshot(s)
    ReDim Preserve m_Undo(0 To m_UndoCount)
    m_Undo(m_UndoCount) = s
    m_UndoCount = m_UndoCount + 1
    ' clear redo
    m_RedoCount = 0
    Erase m_Redo
End Sub

Private Sub cmdUndo_Click()
    Dim sCur As String
    If m_UndoCount <= 0 Then Exit Sub
    Call Snapshot(sCur)
    ReDim Preserve m_Redo(0 To m_RedoCount)
    m_Redo(m_RedoCount) = sCur
    m_RedoCount = m_RedoCount + 1
    m_UndoCount = m_UndoCount - 1
    Call RestoreSnapshot(m_Undo(m_UndoCount))
End Sub

Private Sub cmdRedo_Click()
    Dim sCur As String
    If m_RedoCount <= 0 Then Exit Sub
    Call Snapshot(sCur)
    ReDim Preserve m_Undo(0 To m_UndoCount)
    m_Undo(m_UndoCount) = sCur
    m_UndoCount = m_UndoCount + 1
    m_RedoCount = m_RedoCount - 1
    Call RestoreSnapshot(m_Redo(m_RedoCount))
End Sub

Private Sub cboZoom_Click()
    If cboZoom.ListIndex < 0 Then Exit Sub
    m_Zoom = cboZoom.ItemData(cboZoom.ListIndex) / 100#
    Call Redraw
End Sub

Private Sub chkGrid_Click()
    Call Redraw
End Sub

Private Sub Form_KeyDown(KeyCode As Integer, Shift As Integer)
    If (Shift And vbCtrlMask) <> 0 Then
        If KeyCode = vbKeyZ Then cmdUndo_Click: KeyCode = 0
        If KeyCode = vbKeyY Then cmdRedo_Click: KeyCode = 0
        If KeyCode = vbKeyS Then cmdSave_Click: KeyCode = 0
    End If
End Sub

Private Sub cmdClose_Click()
    Unload Me
End Sub
