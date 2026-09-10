VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
  Persistable = 0  'NotPersistable
  DataBindingBehavior = 0  'vbNone
  DataSourceBehavior = 0   'vbNone
  MTSTransactionMode = 0   'NotAnMTSObject
END
Attribute VB_Name = "clsLayoutCacheEntry"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
'===============================================================================
' Cache bag for one layout.
' VB6 cannot declare Public arrays in class modules — use Collection instead.
'===============================================================================
Option Explicit

Public LayoutID As Long
Public BankID As Long
Public LayoutName As String
Public ChequeWidth As Double
Public ChequeHeight As Double
Public TopMargin As Double
Public LeftMargin As Double
Public PrinterDPI As Long
Public PaperOrientation As Long
Public PaperSizeName As String
Public DateFormatCode As String
Public AmountFormatCode As String
Public CurrencyPrefix As String
Public ShowCurrencyPrefix As Boolean
Public PayeeCaseMode As Long
Public PayeeMaxLength As Long
Public PayeeWrap As Boolean
Public PayeeAutoShrink As Boolean
Public AutoCenter As Boolean
Public Active As Boolean

Public Loaded As Boolean

Private m_Objects As Collection

Private Sub Class_Initialize()
    Set m_Objects = New Collection
End Sub

Private Sub Class_Terminate()
    Set m_Objects = Nothing
End Sub

Public Property Get ObjectCount() As Long
    ObjectCount = m_Objects.Count
End Property

Public Property Get LayoutObject(ByVal Index As Long) As clsLayoutObject
    ' 0-based index to match layout manager arrays
    Set LayoutObject = m_Objects(Index + 1)
End Property

Public Sub ClearObjects()
    Dim i As Long
    For i = m_Objects.Count To 1 Step -1
        m_Objects.Remove i
    Next i
End Sub

Public Sub AddObject(ByVal o As clsLayoutObject)
    m_Objects.Add o
End Sub
