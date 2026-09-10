-- Prefer the Python tool (guest JSON + OTP tables + CUST_SMS):
--   venv\Scripts\python.exe scripts\reset_otp_for_mobile.py 03XXXXXXXXX
--
-- This SQL file only clears customer_app_otp + SMS_DB_ OTP rows.
-- How to use:
--   1. Change @Mobile to the number you want to reset (any of these forms is OK):
--        03218439550
--        3218439550
--        923218439550
--   2. Run this script on database nsds2626.
--
USE [nsds2626];
GO

SET NOCOUNT ON;

DECLARE @Mobile NVARCHAR(30) = N'03218439550';  -- <<< put the test number here
DECLARE @Digits NVARCHAR(30);
DECLARE @Key VARCHAR(10);
DECLARE @Recipient92 VARCHAR(15);

SET @Digits = REPLACE(REPLACE(REPLACE(REPLACE(ISNULL(@Mobile, N''), N'+', N''), N'-', N''), N' ', N''), NCHAR(9), N'');
IF LEFT(@Digits, 2) = N'00'
    SET @Digits = SUBSTRING(@Digits, 3, 30);

IF LEN(@Digits) < 10
BEGIN
    RAISERROR(N'Enter a mobile number with at least 10 digits.', 16, 1);
    RETURN;
END;

SET @Key = RIGHT(@Digits, 10);
SET @Recipient92 = '92' + @Key;

PRINT 'Resetting OTP for mobile_key = ' + @Key;

-- 1) Customer app / ERP OTP records (PENDING, VERIFIED, etc.)
DELETE FROM dbo.customer_app_otp
WHERE mobile_key = @Key
   OR RIGHT(REPLACE(ISNULL(mobile_display, ''), '+', ''), 10) = @Key;

PRINT 'customer_app_otp rows deleted: ' + CAST(@@ROWCOUNT AS VARCHAR(10));

-- 2) OTP SMS queue rows for this number (so you can confirm a NEW insert)
DELETE FROM dbo.SMS_DB_
WHERE (
        RIGHT(REPLACE(REPLACE(ISNULL(RECIPIENT, N''), N'+', N''), N' ', N''), 10) = @Key
     OR REPLACE(ISNULL(RECIPIENT, N''), N'+', N'') = @Recipient92
  )
  AND (
        BODY LIKE N'Your verification code is %'
     OR BODY LIKE N'%verification code%'
  );

PRINT 'SMS_DB_ OTP rows deleted: ' + CAST(@@ROWCOUNT AS VARCHAR(10));

-- Check leftover
SELECT
    (SELECT COUNT(*) FROM dbo.customer_app_otp WHERE mobile_key = @Key) AS otp_rows_left,
    (SELECT COUNT(*)
     FROM dbo.SMS_DB_
     WHERE RIGHT(REPLACE(REPLACE(ISNULL(RECIPIENT, N''), N'+', N''), N' ', N''), 10) = @Key
       AND BODY LIKE N'%verification code%') AS sms_otp_rows_left;
GO
