Attribute VB_Name = "modChequeEnums"
'===============================================================================
' Enterprise Cheque Printing — Enumerations & Constants
' Keep print engine independent of UI; all layout data from database.
'===============================================================================
Option Explicit

'--- Object codes (must match CHEQUE_LAYOUT_DETAIL.ObjectCode)
Public Const CHQ_OBJ_PAYEE_NAME As String = "PAYEE_NAME"
Public Const CHQ_OBJ_AMOUNT As String = "AMOUNT"
Public Const CHQ_OBJ_AMOUNT_WORDS As String = "AMOUNT_WORDS"
Public Const CHQ_OBJ_CHEQUE_DATE As String = "CHEQUE_DATE"
Public Const CHQ_OBJ_DATE_DD As String = "DATE_DD"
Public Const CHQ_OBJ_DATE_MM As String = "DATE_MM"
Public Const CHQ_OBJ_DATE_YYYY As String = "DATE_YYYY"
Public Const CHQ_OBJ_CROSS_MARK As String = "CROSS_MARK"
Public Const CHQ_OBJ_AC_PAYEE As String = "AC_PAYEE"
Public Const CHQ_OBJ_BEARER As String = "BEARER"
Public Const CHQ_OBJ_COMPANY_NAME As String = "COMPANY_NAME"
Public Const CHQ_OBJ_VOUCHER_NO As String = "VOUCHER_NO"
Public Const CHQ_OBJ_NARRATION As String = "NARRATION"
Public Const CHQ_OBJ_CUSTOM_TEXT As String = "CUSTOM_TEXT"
Public Const CHQ_OBJ_SIGNATURE As String = "SIGNATURE_AREA"
Public Const CHQ_OBJ_MICR_IGNORE As String = "MICR_IGNORE"
Public Const CHQ_OBJ_LOGO As String = "LOGO"
Public Const CHQ_OBJ_WATERMARK As String = "WATERMARK"
Public Const CHQ_OBJ_QR_CODE As String = "QR_CODE"

'--- Status codes
Public Const CHQ_STATUS_DRAFT As String = "Draft"
Public Const CHQ_STATUS_PRINTED As String = "Printed"
Public Const CHQ_STATUS_REPRINTED As String = "Reprinted"
Public Const CHQ_STATUS_CANCELLED As String = "Cancelled"
Public Const CHQ_STATUS_VOIDED As String = "Voided"
Public Const CHQ_STATUS_CLEARED As String = "Cleared"
Public Const CHQ_STATUS_BOUNCED As String = "Bounced"

'--- Audit actions
Public Const CHQ_ACT_PRINT As String = "PRINT"
Public Const CHQ_ACT_REPRINT As String = "REPRINT"
Public Const CHQ_ACT_CANCEL As String = "CANCEL"
Public Const CHQ_ACT_VOID As String = "VOID"
Public Const CHQ_ACT_PREVIEW As String = "PREVIEW"
Public Const CHQ_ACT_EXPORT_PDF As String = "EXPORT_PDF"
Public Const CHQ_ACT_EXPORT_IMG As String = "EXPORT_IMG"

'--- Permissions
Public Const CHQ_PERM_PRINT As String = "cheque.print"
Public Const CHQ_PERM_REPRINT As String = "cheque.reprint"
Public Const CHQ_PERM_PREVIEW As String = "cheque.preview"
Public Const CHQ_PERM_LAYOUT_CREATE As String = "cheque.layout.create"
Public Const CHQ_PERM_LAYOUT_EDIT As String = "cheque.layout.edit"
Public Const CHQ_PERM_LAYOUT_DELETE As String = "cheque.layout.delete"
Public Const CHQ_PERM_CANCEL As String = "cheque.cancel"
Public Const CHQ_PERM_EXPORT_PDF As String = "cheque.export_pdf"
Public Const CHQ_PERM_CALIBRATE As String = "cheque.calibrate"
Public Const CHQ_PERM_BATCH As String = "cheque.batch"
Public Const CHQ_PERM_HISTORY As String = "cheque.history"

'--- Preference keys
Public Const CHQ_PREF_LAST_PRINTER As String = "LAST_PRINTER"
Public Const CHQ_PREF_PRINTER_MODE As String = "PRINTER_MODE"
Public Const CHQ_PREF_LAST_LAYOUT As String = "LAST_LAYOUT"

Public Enum eChqAlignment
    chqAlignLeft = 0
    chqAlignCenter = 1
    chqAlignRight = 2
End Enum

Public Enum eChqOrientation
    chqPortrait = 1
    chqLandscape = 2
End Enum

Public Enum eChqPayeeCase
    chqCaseOriginal = 1
    chqCaseUpper = 2
    chqCaseProper = 3
End Enum

Public Enum eChqPrinterMode
    chqPrinterWindowsDefault = 1
    chqPrinterBankDefault = 2
    chqPrinterLastUsed = 3
    chqPrinterSelect = 4
End Enum

Public Enum eChqDateFormat
    chqDateDdMmmYyyy = 1   ' 11-Aug-2026
    chqDateSlash = 2       ' 11/08/2026
    chqDateIso = 3         ' 2026-08-11
    chqDateSpaced = 4      ' 11      08      2026
    chqDateBoxes = 5       ' separate DD/MM/YYYY objects
End Enum

'--- Design units
Public Const CHQ_MM_PER_INCH As Double = 25.4
Public Const CHQ_TWIPS_PER_INCH As Double = 1440#

'--- Designer
Public Const CHQ_GRID_SNAP_MM As Double = 0.5
Public Const CHQ_DESIGNER_BASE_DPI As Long = 96

'--- Error codes (vbObjectError range)
Public Const CHQ_ERR_BASE As Long = vbObjectError + 26000
Public Const CHQ_ERR_LAYOUT_MISSING As Long = CHQ_ERR_BASE + 1
Public Const CHQ_ERR_NO_PERMISSION As Long = CHQ_ERR_BASE + 2
Public Const CHQ_ERR_ALREADY_PRINTED As Long = CHQ_ERR_BASE + 3
Public Const CHQ_ERR_PRINTER As Long = CHQ_ERR_BASE + 4
Public Const CHQ_ERR_INVALID_COORD As Long = CHQ_ERR_BASE + 5
Public Const CHQ_ERR_DATABASE As Long = CHQ_ERR_BASE + 6
Public Const CHQ_ERR_NO_DATA As Long = CHQ_ERR_BASE + 7
