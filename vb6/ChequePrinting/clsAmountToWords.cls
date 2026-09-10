VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
  Persistable = 0  'NotPersistable
  DataBindingBehavior = 0  'vbNone
  DataSourceBehavior = 0   'vbNone
  MTSTransactionMode = 0   'NotAnMTSObject
END
Attribute VB_Name = "clsAmountToWords"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
'===============================================================================
' Convert numeric amounts to English words for cheque printing.
' Supports PKR, USD, EUR, SAR, AED (major/minor units).
'===============================================================================
Option Explicit

Private Type tCurrencyWords
    Code As String
    MajorSingular As String
    MajorPlural As String
    MinorSingular As String
    MinorPlural As String
    MinorScale As Long   ' usually 100
End Type

Private m_Currencies() As tCurrencyWords
Private m_Count As Long

Private Sub Class_Initialize()
    ReDim m_Currencies(0 To 7)
    m_Count = 0
    AddCurrency "PKR", "Rupee", "Rupees", "Paisa", "Paisa", 100
    AddCurrency "USD", "Dollar", "Dollars", "Cent", "Cents", 100
    AddCurrency "EUR", "Euro", "Euros", "Cent", "Cents", 100
    AddCurrency "SAR", "Riyal", "Riyals", "Halala", "Halalas", 100
    AddCurrency "AED", "Dirham", "Dirhams", "Fils", "Fils", 100
    AddCurrency "GBP", "Pound", "Pounds", "Penny", "Pence", 100
End Sub

Private Sub AddCurrency(ByVal sCode As String, ByVal sMajS As String, ByVal sMajP As String, _
                        ByVal sMinS As String, ByVal sMinP As String, ByVal lScale As Long)
    With m_Currencies(m_Count)
        .Code = UCase$(sCode)
        .MajorSingular = sMajS
        .MajorPlural = sMajP
        .MinorSingular = sMinS
        .MinorPlural = sMinP
        .MinorScale = lScale
    End With
    m_Count = m_Count + 1
End Sub

Private Function FindCurrency(ByVal sCode As String) As Long
    Dim i As Long
    sCode = UCase$(Trim$(sCode))
    For i = 0 To m_Count - 1
        If m_Currencies(i).Code = sCode Then
            FindCurrency = i
            Exit Function
        End If
    Next i
    FindCurrency = 0 ' default PKR
End Function

Public Function ToWords(ByVal dblAmount As Double, Optional ByVal sCurrency As String = "PKR", _
                        Optional ByVal bAppendOnly As Boolean = True) As String
    Dim idx As Long
    Dim lMajor As Long
    Dim lMinor As Long
    Dim sMajor As String
    Dim sMinor As String
    Dim sOut As String
    Dim dblAbs As Double
    
    idx = FindCurrency(sCurrency)
    dblAbs = Abs(Round(dblAmount, 2))
    lMajor = Fix(dblAbs)
    lMinor = CLng(Round((dblAbs - lMajor) * m_Currencies(idx).MinorScale, 0))
    If lMinor >= m_Currencies(idx).MinorScale Then
        lMajor = lMajor + 1
        lMinor = 0
    End If
    
    sMajor = NumberToWords(lMajor)
    If Len(sMajor) = 0 Then sMajor = "Zero"
    
    If lMajor = 1 Then
        sOut = sMajor & " " & m_Currencies(idx).MajorSingular
    Else
        sOut = sMajor & " " & m_Currencies(idx).MajorPlural
    End If
    
    If lMinor > 0 Then
        sMinor = NumberToWords(lMinor)
        If lMinor = 1 Then
            sOut = sOut & " and " & sMinor & " " & m_Currencies(idx).MinorSingular
        Else
            sOut = sOut & " and " & sMinor & " " & m_Currencies(idx).MinorPlural
        End If
    End If
    
    If bAppendOnly Then sOut = sOut & " Only"
    If dblAmount < 0 Then sOut = "Minus " & sOut
    ToWords = sOut
End Function

Private Function NumberToWords(ByVal lNumber As Long) As String
    Dim s As String
    If lNumber = 0 Then
        NumberToWords = vbNullString
        Exit Function
    End If
    If lNumber < 0 Then
        NumberToWords = "Minus " & NumberToWords(Abs(lNumber))
        Exit Function
    End If
    
    If lNumber >= 10000000 Then ' Crore (South Asian) — also works for large PKR
        s = NumberToWords(lNumber \ 10000000) & " Crore"
        If (lNumber Mod 10000000) > 0 Then s = s & " " & NumberToWords(lNumber Mod 10000000)
        NumberToWords = Trim$(s)
        Exit Function
    End If
    
    If lNumber >= 100000 Then ' Lakh
        s = NumberToWords(lNumber \ 100000) & " Lakh"
        If (lNumber Mod 100000) > 0 Then s = s & " " & NumberToWords(lNumber Mod 100000)
        NumberToWords = Trim$(s)
        Exit Function
    End If
    
    If lNumber >= 1000 Then
        s = NumberToWords(lNumber \ 1000) & " Thousand"
        If (lNumber Mod 1000) > 0 Then s = s & " " & NumberToWords(lNumber Mod 1000)
        NumberToWords = Trim$(s)
        Exit Function
    End If
    
    If lNumber >= 100 Then
        s = NumberToWords(lNumber \ 100) & " Hundred"
        If (lNumber Mod 100) > 0 Then s = s & " " & NumberToWords(lNumber Mod 100)
        NumberToWords = Trim$(s)
        Exit Function
    End If
    
    NumberToWords = UnderHundred(lNumber)
End Function

Private Function UnderHundred(ByVal n As Long) As String
    Dim ones As Variant
    Dim teens As Variant
    Dim tens As Variant
    
    ones = Array("", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine")
    teens = Array("Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen")
    tens = Array("", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety")
    
    If n < 10 Then
        UnderHundred = ones(n)
    ElseIf n < 20 Then
        UnderHundred = teens(n - 10)
    Else
        UnderHundred = tens(n \ 10)
        If (n Mod 10) > 0 Then UnderHundred = UnderHundred & " " & ones(n Mod 10)
    End If
End Function
