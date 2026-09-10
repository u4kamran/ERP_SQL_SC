-- Sample bank + layout (generic Pakistani-style cheque positions in mm)
-- Adjust via Layout Designer / Calibration Wizard for each physical stock.

SET NOCOUNT ON;
GO

DECLARE @BankID INT, @LayoutID INT;

IF NOT EXISTS (SELECT 1 FROM dbo.BANK_MASTER WHERE BankCode = 'SAMPLE_HBL')
BEGIN
    INSERT INTO dbo.BANK_MASTER (CompanyID, BankCode, BankName, Branch, BranchAddress, PaperSize, Active, Remarks, CreatedBy)
    VALUES (1, 'SAMPLE_HBL', 'Sample Habib Bank', 'Main Branch', 'Karachi', 'Custom', 1, 'Seed layout — replace with production coords', 'SYSTEM');
END

SELECT @BankID = BankID FROM dbo.BANK_MASTER WHERE BankCode = 'SAMPLE_HBL';

IF NOT EXISTS (SELECT 1 FROM dbo.CHEQUE_LAYOUT_MASTER WHERE BankID = @BankID AND LayoutName = 'Standard Laser')
BEGIN
    INSERT INTO dbo.CHEQUE_LAYOUT_MASTER (
        BankID, CompanyID, LayoutName, ChequeWidth, ChequeHeight, TopMargin, LeftMargin,
        PrinterDPI, PaperOrientation, PaperSizeName, DateFormatCode, AmountFormatCode,
        CurrencyPrefix, ShowCurrencyPrefix, PayeeCaseMode, PayeeMaxLength, PayeeWrap,
        PayeeAutoShrink, AutoCenter, Active, IsDefault, CreatedBy
    )
    VALUES (
        @BankID, 1, 'Standard Laser', 175.000, 85.000, 5.000, 5.000,
        300, 2, 'Custom', 'DD-MMM-YYYY', '#,##0.00',
        'PKR', 0, 2, 80, 0,
        1, 0, 1, 1, 'SYSTEM'
    );
END

SELECT @LayoutID = LayoutID FROM dbo.CHEQUE_LAYOUT_MASTER WHERE BankID = @BankID AND LayoutName = 'Standard Laser';

-- Clear and reseed detail objects for sample layout
DELETE FROM dbo.CHEQUE_LAYOUT_DETAIL WHERE LayoutID = @LayoutID;

INSERT INTO dbo.CHEQUE_LAYOUT_DETAIL
    (LayoutID, ObjectName, ObjectCode, XPos, YPos, Width, Height, FontName, FontSize, Bold, Italic, Alignment, Visible, Rotation, PrintOrder, DefaultText, MinFontSize)
VALUES
(@LayoutID, 'Date',            'CHEQUE_DATE',   130.0, 12.0, 40.0, 6.0,  'Arial', 10, 0, 0, 2, 1, 0, 10,  NULL, 7),
(@LayoutID, 'Payee Name',      'PAYEE_NAME',     25.0, 28.0, 110.0, 7.0, 'Arial', 11, 1, 0, 0, 1, 0, 20,  NULL, 7),
(@LayoutID, 'Amount Words',    'AMOUNT_WORDS',   25.0, 40.0, 115.0, 8.0, 'Arial', 9,  0, 0, 0, 1, 0, 30,  NULL, 7),
(@LayoutID, 'Amount',          'AMOUNT',        135.0, 40.0, 35.0, 7.0,  'Arial', 11, 1, 0, 2, 1, 0, 40,  NULL, 8),
(@LayoutID, 'A/C Payee',       'AC_PAYEE',       10.0, 10.0, 30.0, 5.0,  'Arial', 8,  1, 0, 0, 1, 0, 5,   N'A/C PAYEE', NULL),
(@LayoutID, 'Cross Mark',      'CROSS_MARK',     8.0,  8.0,  35.0, 12.0, 'Arial', 8,  0, 0, 0, 1, 0, 6,   NULL, NULL),
(@LayoutID, 'Company Name',    'COMPANY_NAME',   25.0, 55.0, 80.0, 5.0,  'Arial', 8,  0, 0, 0, 0, 0, 50,  NULL, NULL),
(@LayoutID, 'Voucher No',      'VOUCHER_NO',     25.0, 62.0, 40.0, 5.0,  'Arial', 7,  0, 0, 0, 0, 0, 60,  NULL, NULL),
(@LayoutID, 'Narration',       'NARRATION',      25.0, 68.0, 100.0, 5.0, 'Arial', 7,  0, 0, 0, 0, 0, 70,  NULL, NULL),
(@LayoutID, 'Signature Area',  'SIGNATURE_AREA', 120.0, 55.0, 45.0, 20.0,'Arial', 8,  0, 0, 0, 1, 0, 80,  NULL, NULL),
(@LayoutID, 'MICR Ignore',     'MICR_IGNORE',     0.0,  72.0, 175.0, 13.0,'Arial', 6,  0, 0, 0, 0, 0, 99,  NULL, NULL);

-- Grant full rights to typical admin login placeholder (replace USER_ID)
IF NOT EXISTS (SELECT 1 FROM dbo.CHEQUE_PERMISSION WHERE UserID = 'ADMIN' AND PermissionCode = 'cheque.print')
BEGIN
    INSERT INTO dbo.CHEQUE_PERMISSION (UserID, PermissionCode, Allowed)
    SELECT 'ADMIN', v.Code, 1
    FROM (VALUES
        ('cheque.print'),('cheque.reprint'),('cheque.preview'),
        ('cheque.layout.create'),('cheque.layout.edit'),('cheque.layout.delete'),
        ('cheque.cancel'),('cheque.export_pdf'),('cheque.calibrate'),
        ('cheque.batch'),('cheque.history')
    ) v(Code);
END

PRINT 'Sample cheque layout seeded. LayoutID=' + CAST(@LayoutID AS VARCHAR(20));
GO
