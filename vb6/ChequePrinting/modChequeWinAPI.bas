Attribute VB_Name = "modChequeWinAPI"
'===============================================================================
' Windows Printer API declarations for enumeration / default printer detection.
'===============================================================================
Option Explicit

Public Type PRINTER_INFO_2_MIN
    pServerName As Long
    pPrinterName As Long
    pShareName As Long
    pPortName As Long
    pDriverName As Long
    pComment As Long
    pLocation As Long
    pDevMode As Long
    pSepFile As Long
    pPrintProcessor As Long
    pDatatype As Long
    pParameters As Long
    pSecurityDescriptor As Long
    Attributes As Long
    Priority As Long
    DefaultPriority As Long
    StartTime As Long
    UntilTime As Long
    Status As Long
    cJobs As Long
    AveragePPM As Long
End Type

Public Const PRINTER_ENUM_LOCAL As Long = &H2
Public Const PRINTER_ENUM_CONNECTIONS As Long = &H4

Public Const PRINTER_STATUS_PAUSED As Long = &H1
Public Const PRINTER_STATUS_ERROR As Long = &H2
Public Const PRINTER_STATUS_PENDING_DELETION As Long = &H4
Public Const PRINTER_STATUS_PAPER_JAM As Long = &H8
Public Const PRINTER_STATUS_PAPER_OUT As Long = &H10
Public Const PRINTER_STATUS_MANUAL_FEED As Long = &H20
Public Const PRINTER_STATUS_PAPER_PROBLEM As Long = &H40
Public Const PRINTER_STATUS_OFFLINE As Long = &H80
Public Const PRINTER_STATUS_IO_ACTIVE As Long = &H100
Public Const PRINTER_STATUS_BUSY As Long = &H200
Public Const PRINTER_STATUS_PRINTING As Long = &H400
Public Const PRINTER_STATUS_OUTPUT_BIN_FULL As Long = &H800
Public Const PRINTER_STATUS_NOT_AVAILABLE As Long = &H1000
Public Const PRINTER_STATUS_WAITING As Long = &H2000
Public Const PRINTER_STATUS_PROCESSING As Long = &H4000
Public Const PRINTER_STATUS_INITIALIZING As Long = &H8000
Public Const PRINTER_STATUS_WARMING_UP As Long = &H10000
Public Const PRINTER_STATUS_TONER_LOW As Long = &H20000
Public Const PRINTER_STATUS_NO_TONER As Long = &H40000
Public Const PRINTER_STATUS_PAGE_PUNT As Long = &H80000
Public Const PRINTER_STATUS_USER_INTERVENTION As Long = &H100000
Public Const PRINTER_STATUS_OUT_OF_MEMORY As Long = &H200000
Public Const PRINTER_STATUS_DOOR_OPEN As Long = &H400000
Public Const PRINTER_STATUS_SERVER_UNKNOWN As Long = &H800000
Public Const PRINTER_STATUS_POWER_SAVE As Long = &H1000000

Public Declare Function EnumPrinters Lib "winspool.drv" Alias "EnumPrintersA" ( _
    ByVal Flags As Long, ByVal Name As String, ByVal Level As Long, _
    pPrinterEnum As Any, ByVal cbBuf As Long, pcbNeeded As Long, pcReturned As Long) As Long

Public Declare Function GetProfileString Lib "kernel32" Alias "GetProfileStringA" ( _
    ByVal lpAppName As String, ByVal lpKeyName As String, ByVal lpDefault As String, _
    ByVal lpReturnedString As String, ByVal nSize As Long) As Long

Public Declare Function GetComputerName Lib "kernel32" Alias "GetComputerNameA" ( _
    ByVal lpBuffer As String, nSize As Long) As Long

Public Declare Function lstrlenA Lib "kernel32" (ByVal lpString As Long) As Long

Public Declare Sub CopyMemory Lib "kernel32" Alias "RtlMoveMemory" ( _
    Destination As Any, Source As Any, ByVal Length As Long)

Public Declare Function GlobalLock Lib "kernel32" (ByVal hMem As Long) As Long
Public Declare Function GlobalUnlock Lib "kernel32" (ByVal hMem As Long) As Long
Public Declare Function GlobalAlloc Lib "kernel32" (ByVal wFlags As Long, ByVal dwBytes As Long) As Long
Public Declare Function GlobalFree Lib "kernel32" (ByVal hMem As Long) As Long

Public Const GMEM_FIXED As Long = &H0
Public Const GMEM_ZEROINIT As Long = &H40

'--- Pointer to ANSI string helper
Public Function PtrToStringA(ByVal lPtr As Long) As String
    Dim nLen As Long
    Dim sBuf As String
    If lPtr = 0 Then
        PtrToStringA = vbNullString
        Exit Function
    End If
    nLen = lstrlenA(lPtr)
    If nLen <= 0 Then
        PtrToStringA = vbNullString
        Exit Function
    End If
    sBuf = String$(nLen, vbNullChar)
    CopyMemory ByVal sBuf, ByVal lPtr, nLen
    PtrToStringA = sBuf
End Function

Public Function ChequeComputerName() As String
    Dim sBuf As String
    Dim nSize As Long
    nSize = 255
    sBuf = String$(nSize, vbNullChar)
    If GetComputerName(sBuf, nSize) <> 0 Then
        ChequeComputerName = Left$(sBuf, nSize)
    Else
        ChequeComputerName = Environ$("COMPUTERNAME")
    End If
End Function

Public Function WindowsDefaultPrinterName() As String
    Dim sBuf As String
    Dim nRet As Long
    Dim nComma As Long
    sBuf = String$(512, vbNullChar)
    nRet = GetProfileString("windows", "device", "", sBuf, Len(sBuf))
    If nRet > 0 Then
        sBuf = Left$(sBuf, nRet)
        nComma = InStr(1, sBuf, ",")
        If nComma > 0 Then
            WindowsDefaultPrinterName = Left$(sBuf, nComma - 1)
        Else
            WindowsDefaultPrinterName = sBuf
        End If
    End If
End Function

Public Function FriendlyPrinterStatus(ByVal lStatus As Long) As String
    If lStatus = 0 Then
        FriendlyPrinterStatus = "Ready"
        Exit Function
    End If
    If (lStatus And PRINTER_STATUS_OFFLINE) <> 0 Then FriendlyPrinterStatus = "Printer Offline": Exit Function
    If (lStatus And PRINTER_STATUS_PAPER_JAM) <> 0 Then FriendlyPrinterStatus = "Paper Jam": Exit Function
    If (lStatus And PRINTER_STATUS_PAPER_OUT) <> 0 Then FriendlyPrinterStatus = "No Paper": Exit Function
    If (lStatus And PRINTER_STATUS_PAPER_PROBLEM) <> 0 Then FriendlyPrinterStatus = "Paper Problem": Exit Function
    If (lStatus And PRINTER_STATUS_ERROR) <> 0 Then FriendlyPrinterStatus = "Printer Error": Exit Function
    If (lStatus And PRINTER_STATUS_PAUSED) <> 0 Then FriendlyPrinterStatus = "Paused": Exit Function
    If (lStatus And PRINTER_STATUS_BUSY) <> 0 Then FriendlyPrinterStatus = "Busy": Exit Function
    If (lStatus And PRINTER_STATUS_NOT_AVAILABLE) <> 0 Then FriendlyPrinterStatus = "Not Available": Exit Function
    If (lStatus And PRINTER_STATUS_USER_INTERVENTION) <> 0 Then FriendlyPrinterStatus = "Needs Attention": Exit Function
    FriendlyPrinterStatus = "Status Code " & CStr(lStatus)
End Function
