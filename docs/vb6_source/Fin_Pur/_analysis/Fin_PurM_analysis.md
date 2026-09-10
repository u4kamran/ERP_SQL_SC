# Analysis: Fin_PurM.frm
Caption: Abc Company
ClientSize: 9750 x 7665
Controls: 70
Procedures: 35
SQL snippets: 176
MsgBox lines: 44

## Controls
| Name | Type | Caption/Text | Left | Top | Width | Height | TabIndex | Visible | Enabled | Locked |
|---|---|---|---|---|---|---|---|---|---|---|
| cmdPurOrder | VB.CommandButton | Pur O&der | 4905 | 5670 | 1125 | 375 | 66 | True | True |  |
| Command1 | VB.CommandButton | &Check | 3780 | 5670 | 1125 | 375 | 65 | True | True |  |
| CommonDialog1 | MSComDlg.CommonDialog |  | 5535 | 5130 |  |  |  | True | True |  |
| cmdDownload | VB.CommandButton | Do&wnload | 4905 | 6075 | 1125 | 375 | 64 | True | True |  |
| cmdUploadFile | VB.CommandButton | &Upload | 3780 | 6075 | 1125 | 375 | 63 | True | True |  |
| cmdPrintGrid | VB.CommandButton | &Print Gird | 4890 | 6480 | 1170 | 375 | 60 | True | 0   'False |  |
| grd | VSFlex7LCtl.VSFlexGrid |  | 330 | 1305 | 11955 | 3780 | 10 | 0   'False | -1  'True |  |
| CmdShowItem | VB.CommandButton | Show Item | 3713 | 6480 | 1170 | 375 | 59 | True | True |  |
| txtCoID | VB.TextBox |  | 1170 | 7245 | 1110 | 360 | 21 | True | True |  |
| cmdAssignCo | VB.CommandButton | Assi&gn Co | 45 | 7245 | 1125 | 375 | 20 | True | True |  |
| FrameAddress | VB.Frame |  | 2835 | 1605 | 5175 | 1575 | 48 | 0   'False | True |  |
| TxtCityID | VB.TextBox |  | 165 | 1185 | 780 | 285 | 53 | 0   'False | True |  |
| TxtAddress | VB.TextBox |  | 165 | 525 | 4860 | 315 | 52 | 0   'False | True |  |
| TxtStaxID | VB.TextBox |  | 165 | 870 | 3510 | 285 | 51 | 0   'False | True |  |
| TxtDesc | VB.TextBox |  | 165 | 210 | 4860 | 285 | 50 | 0   'False | True |  |
| TxtCityTitle | VB.TextBox |  | 975 | 1185 | 2700 | 285 | 49 | 0   'False | True | -1  'True |
| CmdShowAddr | VB.CommandButton | S&how Address | 4343 | 6855 | 1170 | 375 | 18 | True | True |  |
| CmdDiscount | VB.CommandButton | Discoun&t | 5513 | 6855 | 1170 | 375 | 19 | True | True |  |
| TxtTime | VB.TextBox |  | 7200 | 945 | 885 | 330 | 6 | True | True |  |
| TxtGPID | VB.TextBox |  | 7200 | 615 | 885 | 315 | 4 | True | True |  |
| CboPayment | VB.ComboBox |  | 8115 | 615 | 1590 | 315 | 7 | True | True |  |
| TxtID | VB.TextBox |  | 945 | 945 | 1485 | 330 | 9 | True | True |  |
| CmdAddTrans | VB.CommandButton | &Add Trans. | 3038 | 6855 | 1305 | 375 | 13 | True | True |  |
| TxtRemarks | VB.TextBox |  | 885 | 5130 | 3675 | 315 | 12 | True | True |  |
| VGrid | MSFlexGridLib.MSFlexGrid |  | 105 | 1305 | 9600 | 3780 | 22 | True | True |  |
| TxtDocDAte | MSComCtl2.DTPicker |  | 2490 | 615 | 1530 | 315 | 2 | True | True |  |
| TxtDocID | VB.TextBox |  | 945 | 615 | 1485 | 315 | 1 | True | True |  |
| CmdDelete | VB.CommandButton | &Delete | 4868 | 7260 | 1125 | 375 | 16 | True | True |  |
| CmdClear | VB.CommandButton | Clea&r | 3728 | 7260 | 1125 | 375 | 15 | True | True |  |
| CmdSave | VB.CommandButton | &Save | 2588 | 7260 | 1125 | 375 | 14 | True | True |  |
| CmdClose | VB.CommandButton | &Close | 6008 | 7260 | 1125 | 375 | 17 | True | True |  |
| Image1 | VB.Image |  | 9810 | 5220 | 2460 | 2205 |  | True | True |  |
| LblOffInvDisc | VB.Label | 0.00 | 8190 | 6795 | 1485 | 285 | 62 | True | True |  |
| Label15 | VB.Label | OFF Inv Disc: | 6945 | 6840 | 1200 | 195 | 61 | True | True |  |
| Label1 | VB.Label | &GRN ID : | 45 | 675 | 870 | 195 | 0 | True | True |  |
| Label4 | VB.Label | Su&pplier ID : | 45 | 1020 | 870 | 195 | 8 | True | True |  |
| LStaxExclAmt | VB.Label | 0.00 | 8190 | 5805 | 1485 | 285 | 58 | True | True |  |
| Label10 | VB.Label | S-Tax Excl. Amt : | 6930 | 5850 | 1215 | 195 | 57 | True | True |  |
| LblDiscount | VB.Label | 0.00 | 885 | 5490 | 1215 | 285 | 56 | True | True |  |
| Label3 | VB.Label | Discount : | 6930 | 5535 | 1215 | 195 | 55 | True | True |  |
| LDiscount | VB.Label | 0.00 | 8190 | 5490 | 1485 | 285 | 54 | True | True |  |
| Label13 | VB.Label | Net Amount : | 6930 | 7185 | 1215 | 195 | 47 | True | True |  |
| Label5 | VB.Label | Included : | 6930 | 6510 | 1215 | 195 | 46 | True | True |  |
| Label9 | VB.Label | S-Tax Receivable : | 6930 | 6180 | 1215 | 195 | 45 | True | True |  |
| Label12 | VB.Label | Gross Amt : | 6930 | 5205 | 1215 | 195 | 44 | True | True |  |
| Label8 | VB.Label | Discount  : | 105 | 5535 | 765 | 195 | 43 | True | True |  |
| Label11 | VB.Label | Charges  : | 105 | 5850 | 765 | 195 | 42 | True | True |  |
| LblCharges | VB.Label | 0.00 | 885 | 5820 | 1215 | 285 | 41 | True | True |  |
| LblDiff | VB.Label | 0.00 | 885 | 6150 | 1215 | 285 | 40 | True | True |  |
| Label14 | VB.Label | Diff : | 105 | 6180 | 765 | 195 | 39 | True | True |  |
| HDiscount | VB.Label |  | 2295 | 5580 | 525 | 210 | 38 | 0   'False | True |  |
| HOtherDed | VB.Label |  | 2340 | 5940 | 525 | 210 | 37 | 0   'False | True |  |
| HClaim | VB.Label |  | 2385 | 6210 | 525 | 210 | 36 | 0   'False | True |  |
| HLoading | VB.Label |  | 2025 | 6705 | 525 | 210 | 35 | 0   'False | True |  |
| HCarriage | VB.Label |  | 2250 | 6480 | 525 | 210 | 34 | 0   'False | True |  |
| HOtherCharges | VB.Label |  | 3015 | 5625 | 525 | 210 | 33 | 0   'False | True |  |
| Label6 | VB.Label | Ref # : | 6615 | 675 | 525 | 195 | 3 | True | True |  |
| Label7 | VB.Label | Time : | 6615 | 1020 | 525 | 195 | 5 | True | True |  |
| mNetAmount | VB.Label | 0.00 | 8190 | 7140 | 1485 | 285 | 32 | True | True |  |
| mTAmount | VB.Label | 0.00 | 8190 | 6465 | 1485 | 285 | 31 | True | True |  |
| mSalesTax | VB.Label | 0.00 | 8190 | 6135 | 1485 | 285 | 30 | True | True |  |
| LblRegistration | VB.Label |  | 8115 | 945 | 1590 | 330 | 29 | True | True |  |
| TxtTitle | VB.Label |  | 2490 | 945 | 3705 | 330 | 28 | True | True |  |
| mQty | VB.Label | 0.00 | 5880 | 5160 | 1005 | 285 | 27 | True | True |  |
| mAmount | VB.Label | 0.00 | 8190 | 5160 | 1485 | 285 | 26 | True | True |  |
| Label2 | VB.Label | &Remarks : | 150 | 5205 | 720 | 195 | 11 | True | True |  |
| Line1 | VB.Label |  | 15 | 15 | 9780 | 30 | 25 | True | True |  |
| Line2 | VB.Label | Purchase Receipt | 0 | 30 | 9825 | 495 | 24 | True | True |  |
| Line3 | VB.Label |  | 0 | 540 | 9795 | 30 | 23 | True | True |  |

## Procedures
- Function CalDiscount
- Function DeleteRow
- Sub UpdateBalance
- Function VGridClear
- Sub CmdAddTrans_Click
- Sub cmdAssignCo_Click
- Sub CmdDelete_Click
- Sub CmdDiscount_Click
- Sub cmdDownload_Click
- Sub cmdPrintGrid_Click
- Sub cmdPurOrder_Click
- Sub CmdSave_Click
- Sub CmdClear_Click
- Sub cmdClose_Click
- Sub Command2_Click
- Sub CmdShowAddr_Click
- Sub CmdShowItem_Click
- Sub Command1_Click
- Sub cmdUploadFile_Click
- Sub Form_DblClick
- Sub Form_Load
- Sub grd_KeyDown
- Sub TxtCityID_Validate
- Sub txtCoID_DblClick
- Sub TxtGPID_DblClick
- Sub Txtid_GotFocus
- Function clearform
- Sub TxtDocID_KeyPress
- Sub TxtDocID_Validate
- Sub Form_KeyUp
- Sub TxtID_DblClick
- Sub TxtID_KeyDown
- Sub TxtID_Validate
- Sub vGrid_DblClick
- Sub VGrid_KeyUp

## Table / View References
- fin_c001
- fin_c003
- Fin_Doc
- FIN_ITEM
- fin_item
- fin_ldgr
- Fin_Prod_M
- fin_prod_m
- Fin_PurD
- Fin_PurDed
- Fin_PurM
- Fin_Pur_d
- FIN_PUR_D
- fin_pur_d
- Fin_Pur_m
- Fin_Pur_M
- fin_pur_m_doc
- FIN_SUPP_ITEMS
- fin_supp_items
- gl0001
- gl0002
- gl0003
- GL0004
- gl0006
- V_FIN_STOCK_SUPPLIER
- v_fin_stock_supplier
- v_mode
- v_numbering

## MsgBox / User Messages (raw)
- "Month not selected .... ", vbInformation, cSelFormId
- "Limit of Transactions exahausted " & Chr(13) & "Consult default values ...", vbInformation, "Production Receipt"
- "Error in Query contact with Administrator."
- "Process Completed ... "
- "Acess denied contact with administrator.", vbOKOnly + vbInformation, "System message"
- "Document ID: " & TxtDocID & "  has been deleted... "
- "You must have a purchase Document.", vbOKOnly + vbInformation
- "You must have a purchase Document.", vbOKOnly + vbInformation
- "File not found.", vbExclamation
- nCnt1 & " Items Added successfully.", vbOKOnly, vbModal
- "No transaction to slave ", vbInformation, cSelFormId
- "Document/Voucher Date out of range ...  " & Chr(13) & Chr(13) & "Select between  " & cFiscalStart & "  and  " & cFiscalEnd & "  ", vbCritical, cSelFormId
- "Selected 'Month' does not match with Document/Voucher 'Date' ...", vbCritical, cSelFormId
- "Invalid Fiscal: Select 0 for Yearly Document numbering ... ", vbCritical, cSelFormId
- RsDummy!serial_no
- "total debit " & mTotalDebit & "  total credit " & mTotalCredit
- "New Document/Voucher Added. No. " & cDoc_Abbr & " " & str(NewVoucherNo), vbInformation, cSelFormId
- "New Document/Voucher Added. No. " & cDoc_Abbr & " " & MFiscal & "-" & str(NewVoucherNo), vbInformation, cSelFormId
- "Document/Voucher Edited. No. " & cDoc_Abbr & " " & TxtDocID.Text, vbInformation, cSelFormId
- "Document/Voucher Edited. No. " & cDoc_Abbr & " " & MFiscal & "-" & TxtDocID.Text, vbInformation, cSelFormId
- "Click the save button again.", vbOKOnly + vbInformation
- "Click the save button again.", vbOKOnly + vbInformation
- "You must have a purchase Document.", vbOKOnly + vbInformation
- "You must have a purchase Document.", vbOKOnly + vbInformation
- "File does not exist.", vbExclamation
- "File uploaded successfully.", vbInformation
- "Image not found."
- "Access to Book denied, Consult System Administrator for Book Permission ...", vbInformation, cSelFormId
- "Book not found or for Use of Other Modules, please enter another ...", vbInformation, cSelFormId
- "Book is temporarily stoped ...", vbCritical, cSelFormId
- "Item Successfully deleted."
- "Item not Successfully deleted. "
- "City ID not found...", vbInformation, "Address: City ID"
- "Invoice Already opened. To Search Press Clear Button ... ", vbInformation, cSelFormId
- "Permission to Book is denied, Consult Administrator ... ", vbInformation, cSelFormId
- "Acess denied contact with administrator.", vbOKOnly + vbInformation, "System message"
- "Document/Voucher is posted, please re-enter ...", vbCritical, cSelFormId
- "Supplier ID Not Found ..... ", vbInformation, cSelFormId
- "Document/Voucher not found, please re-enter ...", vbInformation, cSelFormId
- "Invalid Month, only '0' or 'Blank' is allowed  ...", vbInformation, cSelFormId
- "Invalid Month, please select 1 - 12 ...", vbInformation, cSelFormId
- Err.Description, vbInformation, cSelFormId
- "Invalid Supplier ID.", vbCritical
- "Supplier ID not found... ", vbInformation, "Purchase Receipt: Supplier ID"

## SQL Snippets (sample)
- `"select * FROM Fin_Pur_d WHERE prod_id = "`
- `"update fin_item set co_id = "`
- `"update fin_item set co_id = "`
- `" Exit Sub TrapError:     Call ShowError(lngError, Me.Caption)  End Sub  Private Sub CmdDelete_Click() On Error GoTo TrapError    '05 Reverse Balance From Inventory    If cFoundFlag = True Then          If Not Mid(Trim(cUPwordStr), 5, 1) `
- `"select * FROM Fin_Pur_d WHERE Serial_No = "`
- `"select * FROM fin_item WHERE item_id = "`
- `"select * FROM gl0003 WHERE Serial_No = "`
- `"select * FROM gl0001 WHERE ac_id = "`
- `"DELETE FROM Fin_Pur_d WHERE Serial_No = "`
- `"DELETE FROM Fin_Pur_m WHERE prod_id = "`
- `" & SerialCode          Con.Execute SQL          SQL = "`
- `" & cDoc_Type          Con.Execute SQL          'see 14A 2-8-2001 09 Delete Old Transactions GL          SQL = "`
- `" & Val(TxtDocID)          Con.Execute SQL          SQL = "`
- `" & Val(TxtDocID)          Con.Execute SQL          Screen.MousePointer = vbDefault          MsgBox "`
- `" & SERVER_IP  'SERVER_NAME                           ConDoc.connectionString = strConDocString     ConDoc.Open               ' Open connection '    cn.connectionString = connectionString '    cn.Open          ' Retrieve file data from the`
- `"select * FROM FIN_SUPP_ITEMS WHERE item_id = "`
- `"insert into fin_supp_items (supplier_id, item_id, stock_bal) values("`
- `"Invalid Fiscal: Select 0 for Yearly Document numbering ... "`
- `"select * FROM Fin_Pur_d WHERE Serial_No = "`
- `"select * FROM fin_item WHERE item_id = "`
- `"select * FROM gl0003 WHERE Serial_No = "`
- `"select * FROM gl0001 WHERE ac_id = "`
- `"DELETE FROM Fin_Pur_d WHERE Serial_No = "`
- `"SELECT * FROM Fin_Pur_m WHERE prod_id = "`
- `"SELECT * FROM fin_prod_m WHERE serial_no = "`
- `"SELECT MAX(prod_id) As [Max_NO] FROM Fin_Pur_M WHERE fiscal = "`
- `"SELECT * from gc0002"`
- `") '        RsDummy.Update '        RsDummy.Close                 ' Add in Master Document/Voucher Table         Rs.AddNew         Rs!serial_no = SerialCode         Rs!prod_id = NewVoucherNo         Rs!fiscal = MFiscal         ' Production T`
- `", Val(HOtherCharges.Caption)) 'CDbl(HOtherCharges.Caption)     '     Rs.Update     Rs.Close           'Integration Portion '12 Voucher GL voucher M    SQL = "`
- `"         Rs!sys_status = 0         Rs!sys_use = 0         Rs!sys_print = 0    End If    Rs!voucher_date = TxtDocDAte.Value    Rs!serial_no = SerialCode    ' ?    Rs!Amount = T_Amount    Rs!Tnot = nCounter - 1    Rs!edit_by = cUserName    `
- `" & SerialCode    Con.Execute SQL    ' Delete Old Transactions from General Ledger    SQL = "`
- `" & SerialCode    Con.Execute SQL    ' '***************************************************************** ' end new logic from Invoice     ' Balance Updation In Master Inventory and Master GL     '13 Voucher Trans Sale/Purchase     'Dim nCnt A`
- `"SELECT * FROM gl0003"`
- `"SELECT * FROM fin_pur_d"`
- `" Then         tmpExpDate = Date       Else         tmpExpDate = Trim(VGrid.Text)     End If                     ' Insert into Invoice Datail Table       lTsale = lTsale + tmpSaleAmt       lTSalesTax = lTSalesTax + tmpStaxAmt       ITDiscou`
- `") = tmpcostAmt       Rs.Update   'Add Supplier and Item values in FIN_SUPP_ITEMS '**********************************************         Dim cSQL As String           SQL = "`
- `"insert into fin_supp_items (supplier_id, item_id, stock_bal) values("`
- `"                 Call UpdateV(cSQL)           End If           RSMAST.Close '**********************************************       '*********************       '14B Update Balance in Master Inventory * for sale reduce the balance *       ' FOR`
- `" & MItem_ID       Set RSMAST = FetchAll(SQL)       If Not (RSMAST.EOF And RSMAST.BOF) Then            ' 29-06-2002 at lahore grapho            If cSTaxType = 0 Then                GL_Integ = RSMAST!gl_pur_id            Else                GL_`
- `" & GL_Integ '            Set RSMastGL = FETCHALL(SQL) '            If RSMastGL.RecordCount > 0 Then '                 RSMastGL.Edit '                 RSMastGL!cbal = RSMastGL!cbal + tmpSaleAmt '                 RSMastGL!Tnot = RSMastGL!Tnot + 1`
- `" & Trim(TxtTitle), 40)       FinLRS.Update '*****************************       ' Append in General Ledger       ' In case cstaxtype = 0 Every sale has transaction Credit Entries       ' In Case Purchase every transaction is debited to purchase`
- `" & TmpTitle ' ? latter decide what to do/ Item Title             RsGL!debit = tmpSaleAmt             RsGL!credit = 0             RsGL!external_id = 0             RsGL!ref_id = 0             RsGL.Update          End If       End If     Next `
- `"     Set RsGL = FetchAll(SQL)     ' Calculate Net Amount Debited to Customer     ' Calculate Net Amount Credited to Supplier     'Change cause FBR     'lNetInvoice = lTsale - (CDbl(LDiscount) + mDiscount) + lTSalesTax + mCharges     lNetInvoic`
- `" & str(NewVoucherNo)       RsGL!adcn = Trim(TxtGPID)       RsGL!debit = 0       RsGL!credit = lNetInvoice       RsGL!external_id = 0       RsGL!ref_id = 0       RsGL.Update     End If       ' Sales Account Cr     '    If mCharges > 0 Then `
- `"          RsGL!adcn = Trim(TxtGPID)          RsGL!debit = 0          RsGL!credit = (CDbl(HDiscount) + CDbl(LDiscount.Caption))          RsGL!external_id = 0          RsGL!ref_id = 0          RsGL.Update       End If             ' Discount A`
- `"          RsGL!adcn = Trim(TxtGPID)          RsGL!debit = 0          RsGL!credit = CDbl(LblOffInvDisc.Caption)          RsGL!external_id = 0          RsGL!ref_id = 0          RsGL.Update       End If              '       If Val(HClaim) > 0`
- `" & Val(txtID) '    Set RSMastGL = FETCHALL(SQL) '    If RSMastGL.RecordCount > 0 Then '        If T_Amount <> 0 Then '            RSMastGL.Edit '            RSMastGL!cbal = RSMastGL!cbal - T_Amount '            RSMastGL!Tnot = RSMastGL!Tnot + `
- `"select * FROM gl0001 WHERE ac_id = "`
- `"DELETE * FROM FIN_PUR_D WHERE ITEM_ID = 0"`
- `"select ac_title, manualid, ITEM_TITLE, TNOT, CQTY, COST_RATE, SALES_RATE,item_id from V_FIN_STOCK_SUPPLIER where supplier_id = "`
- `"select * from v_fin_stock_supplier where supplier_id = "`
- `"EXEC CalculateWeeklyReorderLevel '"`
- `"          ' Execute the stored procedure     Set Cmd = New ADODB.Command     With Cmd         .ActiveConnection = Con         .CommandText = strSQL         .CommandType = adCmdText         Set Rs = .Execute     End With          ' Process`
- `", vbExclamation '''        Exit Sub '''    End If ''' '''    ' Read file data into a byte array '''    Open filePath For Binary As #1 '''    ReDim fileData(LOF(1) - 1) '''    Get #1, , fileData '''    Close #1 ''' '''    ' Get the file nam`
- `"Select File to Save"`
- `"delete from fin_pur_m_doc where prod_id = "`
- `"INSERT INTO  fin_pur_m_doc (prod_id, serial_no, pdf_doc) VALUES (?, ?, ?)"`
- `", adVarBinary, adParamInput, UBound(fileData) + 1, fileData)          ' Execute command     Cmd.Execute          MsgBox "`
- `")          ' Query to fetch the image from the database     Rs.Open "`
- `" ' Temporary path to store image          ' Save the binary data to a file         Open imgData For Binary Access Write As #1         Put #1, , imgByte         Close #1                  ' Load the saved image into the Image control         I`
- `" Then         cmdAssignCo.Visible = False         txtCoID.Visible = False         cmdUploadFile.Visible = False         cmdDownload.Visible = False         Command1.Visible = False     End If               ' mvmode = 1 = Combine     ' Vouc`
- `"select * from fin_c003 where doc_id = 2"`
- `"SELECT * FROM fin_c001 WHERE doc_id = "`
- `"SELECT * FROM GL0004 WHERE sys_type = 1 and book_id = "`
- `"SELECT * FROM GC0003 WHERE l_uid = "`
- `"select * from fin_c003 where doc_id = 2"`
- `"Are you sure to delete."`
- `"delete from fin_supp_items where SUPPLIER_ID = "`
- `"SELECT * FROM City WHERE City_id = "`
- `"SELECT * FROM Fin_Pur_M WHERE prod_id = "`
- `"SELECT * FROM gl0006 WHERE vendor_id = "`
- `"SELECT * FROM City WHERE City_id = "`
- `"SELECT * FROM Fin_Pur_d WHERE Serial_No = "`
- `"select * from FIN_ITEM where item_id="`
- `"SELECT * FROM gl0006 WHERE Vendor_id = "`
- `"Invalid Month, please select 1 - 12 ..."`
- `"SELECT * FROM gl0006 WHERE Vendor_id = "`
- `"SELECT * FROM City WHERE City_id = "`
- `' Delete Old Transactions from General Ledger    SQL = "DELETE FROM gl0003 WHERE Serial_No = " & SerialCode    Con.Execute SQL    '`
- `' Insert into Invoice Datail Table       lTsale = lTsale + tmpSaleAmt       lTSalesTax = lTSalesTax + tmpStaxAmt       ITDiscount = ITDiscount + tmpDiscAmt       ITDiscountOI = ITDiscountOI + tmpDOI_Amt       '`
- `'Update Cost_rate             '`
- `' Update Balance in Master GL       '`
- `'False       EndProperty       MousePointer    =   0       BackColor       =   16248808       ForeColor       =   0       BackColorFixed  =   -2147483633       ForeColorFixed  =   -2147483630       BackColorSel    =   -2147483635       ForeCo`
- `'True       AllowUserResizing=   1       SelectionMode   =   0       GridLines       =   1       GridLinesFixed  =   2       GridLineWidth   =   1       Rows            =   2       Cols            =   3       FixedRows       =   1       Fixe`
- `"       Height          =   375       Left            =   3038       TabIndex        =   13       Top             =   6855       Width           =   1305    End    Begin VB.TextBox TxtRemarks        Height          =   315       Left        `
- `' Sales Tax and Invoice Policy Private mCreditSalesLocalId, mCreditSalesImportId, mCashSalesLocalId, mCashSalesImportId As Double Private mSalesId, mSalesTaxPayableId, mSalesReturnID, mDiscountID, mClaimId, mOtherDedID As Double Private nSTaxAmoun`
- `"ShellExecuteA"`
- `") Exit Function TrapError:     Call ShowError(lngError, Me.Caption) End Function  Private Function DeleteRow()     On Error GoTo TrapError    Dim ValCol1 As String    Dim ValCol2 As String    Dim ValCol3 As String    Dim ValCol4 As Strin`
- `"                          nCounter = nCounter - 1                       End If       Loop    End If Exit Function TrapError:     Call ShowError(lngError, Me.Caption) End Function  Private Sub UpdateBalance() On Error GoTo TrapError    `
- `"Month not selected .... "`
- `'End If    If nCounter <= max_entries Then       lEdit = False       Fin_PurD.Show vbModal, Me       Call UpdateBalance '`
- `'TxtFiscal.Enabled = False         CmdSave.Enabled = True         CmdDelete.Enabled = True         CmdDiscount.Enabled = True       End If    Else         MsgBox "`
- `"select * FROM Fin_Pur_d WHERE prod_id = " & intDocID`
- `"update fin_item set co_id = " & intCoID & ", cost_rate = " & dblCost & " where item_id = "`
- `"update fin_item set co_id = " & intCoID & " where item_id = "`
- `" Exit Sub TrapError:     Call ShowError(lngError, Me.Caption)  End Sub  Private Sub CmdDelete_Click() On Error GoTo TrapError    '`
- `"select * FROM Fin_Pur_d WHERE Serial_No = " & SerialCode`
- `"select * FROM fin_item WHERE item_id = " & DelItemID`
- `'RSMAST.Edit                      RSMAST!Cqty = RSMAST!Cqty - tmpQty                      RSMAST!CAMT = RSMAST!CAMT - tmpAmt                      RSMAST!Tnot = RSMAST!Tnot - 1                      RSMAST!Tnot1 = 0                      RSMAST.Upd`
- `"select * FROM gl0003 WHERE Serial_No = " & SerialCode`
- `"select * FROM gl0001 WHERE ac_id = " & DelAccountID`
- `'RSMAST.Edit                      RSMAST!cbal = RSMAST!cbal - DelDr + DelCr                      RSMAST!Tnot = RSMAST!Tnot - 1                      RSMAST.Update                 End If                 RSMAST.Close                 RsGL.MoveNext`
- `'08 Delete Old Transactions from Detail Inventory Table ?          SQL = "`
- `" & cDoc_Type          Con.Execute SQL          '`
- `"DELETE FROM gl0003 WHERE Serial_No = " & SerialCode & " and book_id = " & cBookID & " and voucher_id = " & Val`
- `"DELETE FROM gl0002 WHERE Serial_No = " & SerialCode & " and book_id = " & cBookID & " and voucher_id = " & Val`
- `"  has been deleted... "`
- `"SELECT pdf_doc FROM fin_pur_m_doc WHERE Prod_ID = " & prodId & " AND Serial_No = " & serialNo`
- `' Open the temporary HTML file in the default browser         ShellExecute 0, "`
- `"select * FROM FIN_SUPP_ITEMS WHERE item_id = " & MItem_ID & "  and supplier_id = " & TxtID`
- `"insert into fin_supp_items (supplier_id, item_id, stock_bal) values(" & TxtID`
- `"                 Call UpdateV(cSQL)                 nCnt1 = nCnt1 + 1           End If           RSMAST.Close     Next           MsgBox nCnt1 & "`
- `"Select between  " & cFiscalStart & "  and  " & cFiscalEnd & "  "`
- `"Selected '`
- `'RSMAST.Edit                  RSMAST!Cqty = RSMAST!Cqty - tmpQty                  RSMAST!CAMT = RSMAST!CAMT - tmpAmt                  RSMAST!Tnot = RSMAST!Tnot - 1                  RSMAST.Update             End If             RSMAST.Close     `
- `'RSMAST.Edit                     RSMAST!cbal = RSMAST!cbal - DelDr + DelCr                     RSMAST!Tnot = RSMAST!Tnot - 1                     RSMAST.Update                End If                RSMAST.Close                RsGL.MoveNext      `
- `'08 Delete Old Transactions Purchase Detail         SQL = "`
- `" & SerialCode         Con.Execute SQL         '`
- `"SELECT * FROM fin_prod_m WHERE serial_no = " & SerialCode`
- `"SELECT MAX(prod_id) As [Max_NO] FROM Fin_Pur_M WHERE fiscal = " & MFiscal`
- `'        RsDummy.Update '`
- `'     Rs.Update     Rs.Close           '`
- `"SELECT * FROM gl0002 WHERE serial_no = " & SerialCode`
- `' ?    Rs!Amount = T_Amount    Rs!Tnot = nCounter - 1    Rs!edit_by = cUserName    Rs.Update    Rs.Close    '`
- `'14 Delete Old Transactions from Finished Ledger    SQL = "`
- `" & SerialCode    Con.Execute SQL    '`
- `"DELETE FROM gl0003 WHERE Serial_No = " & SerialCode`
- `"SELECT * FROM fin_ldgr"`
- `") = tmpcostAmt       Rs.Update   '`
- `"                 Call UpdateV(cSQL)           End If           RSMAST.Close '`
- `'14B Update Balance in Master Inventory * for sale reduce the balance *       '`
- `"select * FROM fin_item WHERE item_id = " & MItem_ID`
- `"select * FROM gl0001 WHERE ac_id = " & GL_Integ`
- `'                 RSMastGL.Update '`
- `" & Trim(TxtTitle), 40)       FinLRS.Update '`
- `' ? latter decide what to do/ Item Title             RsGL!debit = tmpSaleAmt             RsGL!credit = 0             RsGL!external_id = 0             RsGL!ref_id = 0             RsGL.Update          End If       End If     Next     Rs.Close`
- `' Purchase Import         If mSalesImportAmt > 0 Then             RsGL.AddNew             RsGL!Voucher_ID = NewVoucherNo             RsGL!book_id = cBookID             RsGL!vdate = TxtDocDAte.Value             RsGL!serial_no = SerialCode      `
- `'RsGL!ac_id = mCreditSalesLocalId             RsGL!Ac_id = mCreditSalesLocalId             RsGL!Narration = TxtTitle             RsGL!adcn = Trim(TxtGPID)             RsGL!debit = mSalesLocalAmt             RsGL!credit = 0             RsGL!exte`
- `' Sales Tax Receivable Dr         If lTSalesTax > 0 Then             RsGL.AddNew             RsGL!Voucher_ID = NewVoucherNo             RsGL!book_id = cBookID             RsGL!vdate = TxtDocDAte.Value             RsGL!serial_no = SerialCode   `
- `' Debit Entries/expenses       If Val(HLoading) > 0 Then          RsGL.AddNew          RsGL!Voucher_ID = NewVoucherNo          RsGL!book_id = cBookID          RsGL!vdate = TxtDocDAte.Value          RsGL!serial_no = SerialCode          RsGL!Ser`
- `'       If Val(HOtherCharges) > 0 Then          RsGL.AddNew          RsGL!Voucher_ID = NewVoucherNo          RsGL!book_id = cBookID          RsGL!vdate = TxtDocDAte.Value          RsGL!serial_no = SerialCode          RsGL!Serial_order = 6    `
- `" & str(NewVoucherNo)       RsGL!adcn = Trim(TxtGPID)       RsGL!debit = 0       RsGL!credit = lNetInvoice       RsGL!external_id = 0       RsGL!ref_id = 0       RsGL.Update     End If       '`
- `"          RsGL!adcn = Trim(TxtGPID)          RsGL!debit = 0          RsGL!credit = (CDbl(HDiscount) + CDbl(LDiscount.Caption))          RsGL!external_id = 0          RsGL!ref_id = 0          RsGL.Update       End If             '`
- `"          RsGL!adcn = Trim(TxtGPID)          RsGL!debit = 0          RsGL!credit = CDbl(LblOffInvDisc.Caption)          RsGL!external_id = 0          RsGL!ref_id = 0          RsGL.Update       End If              '`
- `'       If Val(HOtherDed) > 0 Then          RsGL.AddNew          RsGL!Voucher_ID = NewVoucherNo          RsGL!book_id = cBookID          RsGL!vdate = TxtDocDAte.Value          RsGL!serial_no = SerialCode          RsGL!Serial_order = 11       `
- `"select * FROM gl0001 WHERE ac_id = " & Val`
- `'            RSMastGL.Update '`
- `' Read the newly prepared voucher from gl0003 and update the gl0001 table     '`
- `'RSMAST.Edit                 RSMAST!cbal = RSMAST!cbal + DelDr - DelCr                 RSMAST!Tnot = RSMAST!Tnot + 1                 RSMAST.Update            End If            RSMAST.Close            RsGL.MoveNext        Loop        RsGL.Clos`
- `"select ac_title, manualid, ITEM_TITLE, TNOT, CQTY, COST_RATE, SALES_RATE,item_id from V_FIN_STOCK_SUPPLIER where supplier_id = " & TxtID`