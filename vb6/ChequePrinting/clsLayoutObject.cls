VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
  Persistable = 0  'NotPersistable
  DataBindingBehavior = 0  'vbNone
  DataSourceBehavior = 0   'vbNone
  MTSTransactionMode = 0   'NotAnMTSObject
END
Attribute VB_Name = "clsLayoutObject"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
'===============================================================================
' Single printable layout object (coordinate unit = mm).
'===============================================================================
Option Explicit

Public DetailID As Long
Public LayoutID As Long
Public ObjectName As String
Public ObjectCode As String
Public XPos As Double
Public YPos As Double
Public Width As Double
Public Height As Double
Public FontName As String
Public FontSize As Double
Public Bold As Boolean
Public Italic As Boolean
Public Alignment As eChqAlignment
Public Visible As Boolean
Public Rotation As Integer
Public PrintOrder As Long
Public DefaultText As String
Public ForeColor As Long
Public LineStyle As Integer
Public DataField As String
Public MinFontSize As Double

Public Function CloneMe() As clsLayoutObject
    Dim o As New clsLayoutObject
    Set CloneMe = o
    With o
        .DetailID = DetailID
        .LayoutID = LayoutID
        .ObjectName = ObjectName
        .ObjectCode = ObjectCode
        .XPos = XPos
        .YPos = YPos
        .Width = Width
        .Height = Height
        .FontName = FontName
        .FontSize = FontSize
        .Bold = Bold
        .Italic = Italic
        .Alignment = Alignment
        .Visible = Visible
        .Rotation = Rotation
        .PrintOrder = PrintOrder
        .DefaultText = DefaultText
        .ForeColor = ForeColor
        .LineStyle = LineStyle
        .DataField = DataField
        .MinFontSize = MinFontSize
    End With
End Function
