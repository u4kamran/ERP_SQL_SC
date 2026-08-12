# Analysis: Fin_PurD.frm
Caption: Abc Company
ClientSize: 8400 x 8760
Controls: 67
Procedures: 60
SQL snippets: 37
MsgBox lines: 20

## Controls
| Name | Type | Caption/Text | Left | Top | Width | Height | TabIndex | Visible | Enabled | Locked |
|---|---|---|---|---|---|---|---|---|---|---|
| txtCoID | VB.TextBox |  | 3375 | 3465 | 1605 | 315 | 28 | True | True |  |
| txtNetCost | VB.TextBox |  | 960 | 2025 | 1605 | 360 | 62 | True | 0   'False |  |
| txtOffInvDiscAmt | VB.TextBox |  | 6690 | 3555 | 1650 | 360 | 27 | True | True |  |
| TxtOffInvDiscPer | VB.TextBox |  | 960 | 3150 | 1605 | 360 | 57 | True | 0   'False |  |
| txtMRP | VB.TextBox |  | 960 | 2400 | 1605 | 360 | 18 | True | True | -1  'True |
| txtNoOf | VB.TextBox | 5 | 1455 | 4515 | 1020 | 360 | 47 | True | True | -1  'True |
| txtPQty | VB.TextBox |  | 3375 | 1680 | 1605 | 360 | 8 | True | True |  |
| TxtsRemarks | VB.TextBox |  | 960 | 3885 | 1605 | 360 | 24 | True | True |  |
| Text1 | VB.TextBox |  | 3375 | 2400 | 1605 | 360 | 4 | True | True |  |
| txtUnit | VB.TextBox |  | 3375 | 1335 | 1605 | 360 | 6 | True | True |  |
| TxtPRate | VB.TextBox |  | 3375 | 2040 | 1605 | 360 | 10 | True | True |  |
| txtBarcode | VB.TextBox |  | 3375 | 2775 | 1605 | 360 | 2 | True | True |  |
| TxtStaxRate | VB.TextBox |  | 960 | 3540 | 1605 | 360 | 22 | True | True |  |
| txtDiscAmt | VB.TextBox |  | 6690 | 2040 | 1650 | 360 | 25 | True | True |  |
| txtDiscPer | VB.TextBox |  | 960 | 2760 | 1605 | 360 | 20 | True | 0   'False |  |
| CmdClose | VB.CommandButton | &Close | 7215 | 4515 | 1125 | 375 | 35 | True | True |  |
| CmdSave | VB.CommandButton | &Save | 2640 | 4515 | 1125 | 375 | 30 | True | True |  |
| CmdClear | VB.CommandButton | Clea&r | 3780 | 4515 | 1125 | 375 | 32 | True | True |  |
| CmdItem | VB.CommandButton | &Item | 4920 | 4515 | 1125 | 375 | 33 | True | True |  |
| CmdBalance | VB.CommandButton | Balance | 6075 | 4515 | 1125 | 375 | 34 | True | True |  |
| txtBarcodeWS | VB.TextBox |  | 3375 | 3150 | 1605 | 315 | 0 | True | True |  |
| TxtStaxAmount | VB.TextBox |  | 6690 | 2820 | 1650 | 360 | 26 | True | True |  |
| TxtRate | VB.TextBox |  | 960 | 1680 | 1605 | 360 | 16 | True | True |  |
| TxtQty | VB.TextBox |  | 960 | 1335 | 1605 | 360 | 14 | True | True |  |
| TxtID | VB.TextBox |  | 960 | 990 | 1605 | 360 | 12 | True | True |  |
| grd | VSFlex7LCtl.VSFlexGrid |  | 0 | 4905 | 8265 | 3375 | 46 | True | -1  'True |  |
| TxtExpDate | MSComCtl2.DTPicker |  | 3375 | 3780 | 1605 | 315 | 29 | True | True |  |
| lblCoTitle | VB.Label | Item Title | 3375 | 4140 | 2220 | 330 | 65 | True | True |  |
| Label26 | VB.Label | Co ID : | 2835 | 3525 | 495 | 195 | 31 | True | True |  |
| Label25 | VB.Label | Exp Date : | 2580 | 3840 | 750 | 195 | 64 | True | True |  |
| Label24 | VB.Label | Net Cost : | 210 | 2115 | 705 | 195 | 63 | True | True |  |
| LblOffInvIncludedAmt | VB.Label | 0.00 | 6690 | 3195 | 1650 | 360 | 61 | True | True |  |
| Label23 | VB.Label | Included Amount : | 5280 | 3285 | 1380 | 195 | 60 | True | True |  |
| Label22 | VB.Label | Off InvDisc : | 5775 | 3645 | 885 | 195 | 59 | True | True |  |
| Label21 | VB.Label | Disc% Off  : | 90 | 3240 | 825 | 195 | 58 | True | True |  |
| lblProfitPer | VB.Label | % | 45 | 105 | 1500 | 495 | 56 | 0   'False | True |  |
| Label20 | VB.Label | M.R.P : | 375 | 2490 | 540 | 195 | 17 | True | True |  |
| lblSale | VB.Label | 0.00 | 4995 | 1335 | 1110 | 360 | 45 | True | True |  |
| lblStock | VB.Label | 0 | 4995 | 1710 | 1110 | 360 | 55 | True | True |  |
| Label14 | VB.Label | &Unit : | 2655 | 1418 | 675 | 195 | 5 | True | True |  |
| Label15 | VB.Label | Qua&ntity : | 2655 | 1763 | 675 | 195 | 7 | True | True |  |
| Label16 | VB.Label | R&ate : | 2895 | 2130 | 435 | 195 | 9 | True | True |  |
| Label12 | VB.Label | &Manual : | 2655 | 2483 | 675 | 195 | 3 | True | True |  |
| Label13 | VB.Label | &Barcode : | 2655 | 2858 | 675 | 195 | 1 | True | True |  |
| Label8 | VB.Label | G Amt : | 6135 | 1785 | 525 | 195 | 53 | True | True |  |
| Label7 | VB.Label | Net Amount : | 5730 | 4020 | 930 | 195 | 52 | True | True |  |
| Label10 | VB.Label | Sales Tax Amount : | 5280 | 2910 | 1380 | 195 | 51 | True | True |  |
| Label17 | VB.Label | TO + On InvDisc : | 5370 | 2130 | 1290 | 195 | 50 | True | True |  |
| Label18 | VB.Label | Excluded Amount : | 5280 | 2513 | 1380 | 195 | 49 | True | True |  |
| Label19 | VB.Label | No of Pur Trans : | 105 | 4605 | 1215 | 195 | 48 | True | True |  |
| lblExcludAmt | VB.Label | 0.00 | 6690 | 2430 | 1650 | 360 | 44 | True | True |  |
| Label5 | VB.Label | S-&Tax % : | 240 | 3630 | 675 | 195 | 21 | True | True |  |
| Label11 | VB.Label | Disc% On : | 135 | 2850 | 780 | 195 | 19 | True | True |  |
| Label9 | VB.Label | Sub Title : | 1740 | 585 | 720 | 195 | 43 | True | True |  |
| Label2 | VB.Label | Main Title : | 1680 | 180 | 780 | 195 | 42 | True | True |  |
| LblMainTitle | VB.Label | Main Title | 2535 | 105 | 5820 | 330 | 41 | True | True |  |
| LblSubTitle | VB.Label | SubTitle | 2535 | 525 | 5820 | 330 | 40 | True | True |  |
| LblIncludedAmount | VB.Label | 0.00 | 6690 | 3930 | 1650 | 360 | 39 | True | True |  |
| Label1 | VB.Label | Remar&ks : | 135 | 3975 | 780 | 195 | 23 | True | True |  |
| TxtAmount | VB.Label | 0.00 | 6690 | 1710 | 1650 | 360 | 38 | True | True |  |
| TxtUomTitle | VB.Label | Unit of Measurement | 6690 | 1335 | 1650 | 360 | 37 | True | True |  |
| Label4 | VB.Label | TP Rat&e : | 225 | 1770 | 690 | 195 | 15 | True | True |  |
| Label3 | VB.Label | &Quantity : | 135 | 1425 | 780 | 195 | 13 | True | True |  |
| LblItem | VB.Label | &Item ID : | 135 | 1080 | 780 | 195 | 11 | True | True |  |
| TxtTitle | VB.Label | Item Title | 2805 | 960 | 5550 | 330 | 36 | True | True |  |
| Label6 | VB.Label | UOM : | 5280 | 1365 | 1380 | 195 | 54 | True | True |  |

## Procedures
- Sub Calc_Rate
- Sub PUpdateBalance
- Sub CmdDelete_Click
- Sub cmdPrint_Click
- Sub CmdBalance_Click
- Sub CmdItem_Click
- Sub CmdSave_Click
- Sub Form_Activate
- Sub Form_KeyUp
- Sub Form_Paint
- Sub LblItem_Click
- Sub Text1_KeyPress
- Sub Text1_Validate
- Sub txtBarcode_KeyPress
- Sub txtBarcode_Validate
- Sub txtBarcodeWS_Validate
- Sub txtCoID_DblClick
- Sub txtCoID_GotFocus
- Sub txtCoID_KeyDown
- Sub txtCoID_KeyPress
- Sub txtCoID_Validate
- Sub txtDiscAmt_GotFocus
- Sub txtDiscAmt_KeyPress
- Sub txtDiscAmt_Validate
- Sub txtDiscPer_Change
- Sub txtDiscPer_Validate
- Sub TxtID_DblClick
- Sub CmdClear_Click
- Sub cmdClose_Click
- Sub Form_KeyPress
- Sub Form_KeyDown
- Sub Form_Load
- Function clearform
- Sub TxtItemID_KeyPress
- Sub Txtid_GotFocus
- Sub TxtID_KeyDown
- Sub TxtID_Validate
- Sub txtOffInvDiscAmt_GotFocus
- Sub txtOffInvDiscAmt_KeyPress
- Sub txtOffInvDiscAmt_Validate
- Sub TxtPQty_Change
- Sub TxtPQty_GotFocus
- Sub txtPQty_KeyPress
- Sub TxtPRate_Change
- Sub TxtPRate_KeyPress
- Sub TxtPRate_LostFocus
- Sub TxtQty_GotFocus
- Sub TxtQty_KeyPress
- Sub TxtQty_Validate
- Sub TxtRate_Change
- Sub TxtRate_GotFocus
- Sub TxtRate_KeyDown
- Sub TxtRate_KeyPress
- Sub TxtRate_LostFocus
- Sub TxtStaxAmount_GotFocus
- Sub TxtStaxAmount_KeyPress
- Sub TxtStaxAmount_Validate
- Sub TxtStaxRate_GotFocus
- Sub TxtStaxRate_KeyPress
- Sub TxtStaxRate_Validate

## Table / View References
- Fin_Auto
- fin_c002
- fin_item
- FIN_ITEM
- Fin_Item
- Fin_PurD
- Fin_PurM
- Fin_Pur_D
- FIN_PUR_D
- v_fin_item
- v_FIN_ITEM

## MsgBox / User Messages (raw)
- "Invalid:  Please enter Rate ...  ", vbInformation, "Purchase Receipt"
- "Invalid:  Please enter Quantity ...  ", vbInformation, "Purchase Receipt"
- "Invalid:  Please enter Rate ...  ", vbInformation, "Production Receipt"
- "Invalid:  Please enter Quantity ...  ", vbInformation, "Production Receipt"
- "Invalid:  Please enter Company ID ...  ", vbInformation, "Production Receipt"
- Rs!Inv_id
- "meditrowid = " & mEditRowID & "   icounter +1 = " & iCounter + 1
- "Duplicate: Item ID Already Exists .... ", vbInformation
- "Manual ID not found."
- "Barcode ID not found."
- "Barcode ID not found."
- "Company ID not found... ", vbInformation, "Purchase Receipt: Company ID"
- Err.Description, vbInformation, cSelFormId
- "Invalid ID length ", vbInformation, cSelFormId
- "Item ID is Disabled, Consultant Administrator .... ", vbInformation, cSelFormId
- "Account ID is Diabled, please re-enter another ... ", vbCritical, cSelFormId
- "Item ID not found, please re-enter ... " & Chr(13) & Chr(13) & " Or Main Or Sub Account ID is selected. ", vbInformation, "Production Receipt"
- Err.Description, vbInformation, cSelFormId
- "Invalid:  Please enter Rate ...  ", vbInformation, "Production Receipt"
- "Invalid:  Please enter Quantity ...  ", vbInformation, "Production Receipt"

## SQL Snippets (sample)
- `"select * from FIN_ITEM where item_id="`
- `"update fin_item set disc_p1 = "`
- `"update fin_item set disc_p1 = "`
- `" & Val(TxtStaxAmount)           Debug.Print .CommandText         .Execute     End With                  If Not Val(TxtID) < 0 Then             SQL = "`
- `") ' '                Rs.Update             End If         End If                  Call SaveLogData("`
- `"select * from v_fin_item where manualid = "`
- `"select * from v_fin_item where manualid = "`
- `"select * from v_fin_item where barcodeid = '"`
- `"select * from v_fin_item where barcodeid = '"`
- `"select * from v_fin_item where barcodeid = '"`
- `"select * from v_fin_item where barcodeid_ws = '"`
- `"SELECT * FROM co WHERE co_id = "`
- `"select * from v_fin_item where item_id = "`
- `"select * from v_fin_item where item_id = "`
- `"select * from FIN_ITEM where item_id="`
- `"SELECT * FROM fin_c002 WHERE uom_id = "`
- `"select * from v_FIN_ITEM where item_id="`
- `"select * from FIN_ITEM where item_id="`
- `" Prod_id,doc_date,QTY,((pur_AMT - disc_amt - disc_amt_oi )/QTY) as cost_amt ,rate as TP,item_id from Fin_Pur_D "`
- `" Prod_id,doc_date,QTY,rate as TP,item_id from Fin_Pur_D "`
- `'False       EndProperty       MousePointer    =   0       BackColor       =   16248808       ForeColor       =   0       BackColorFixed  =   -2147483633       ForeColorFixed  =   -2147483630       BackColorSel    =   -2147483635       ForeCo`
- `'True       AllowUserResizing=   1       SelectionMode   =   0       GridLines       =   1       GridLinesFixed  =   2       GridLineWidth   =   1       Rows            =   2       Cols            =   3       FixedRows       =   1       Fixe`
- `")              End If                Exit Sub TrapError:     Call ShowError(lngError, Me.Caption) End Sub Private Sub PUpdateBalance() On Error GoTo TrapError    Dim nCnt As Integer    Dim nQty As Double    Dim nAmount As Double    Di`
- `' other two columns ? Exit Sub TrapError:     Call ShowError(lngError, Me.Caption) End Sub Private Sub CmdDelete_Click() On Error GoTo TrapError      Screen.MousePointer = vbHourglass      Screen.MousePointer = vbDefault      Call clearform`
- `"select * from FIN_ITEM where item_id=" & Val`
- `"update fin_item set disc_p1 = " & CDbl`
- `'                Rs.Update             End If         End If                  Call SaveLogData("`
- `'******************************************************    Call PUpdateBalance    Call clearform Exit Sub TrapError:     Call ShowError(lngError, Me.Caption) End Sub    Private Sub Form_Activate() '`
- `"select * from v_fin_item where manualid = " & CDbl`
- `"select * from v_fin_item where barcodeid = '`
- `"select * from v_fin_item where barcodeid_ws = '`
- `"SELECT * FROM co WHERE co_id = " & Val`
- `"select * from v_fin_item where item_id = " & TxtID`
- `"SELECT * FROM fin_c002 WHERE uom_id = " & mUomID`
- `" Or Main Or Sub Account ID is selected. "`
- `"select * from v_FIN_ITEM where item_id=" & CDbl`
- `"select top " & txtNoOf`