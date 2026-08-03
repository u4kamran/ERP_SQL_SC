VERSION 5.00
Object = "{86CF1D34-0C5F-11D2-A9FC-0000F8754DA1}#2.0#0"; "MSCOMCT2.OCX"
Object = "{5E9E78A0-531B-11CF-91F6-C2863C385E30}#1.0#0"; "MSFLXGRD.OCX"
Begin VB.Form FrmSalesDashboard 
   BorderStyle     =   1  'Fixed Single
   Caption         =   "Sales Dashboard"
   ClientHeight    =   9000
   ClientLeft      =   45
   ClientTop       =   330
   ClientWidth     =   12000
   BeginProperty Font 
      Name            =   "Verdana"
      Size            =   8.25
      Charset         =   0
      Weight          =   700
      Underline       =   0   'False
      Italic          =   0   'False
      Strikethrough   =   0   'False
   EndProperty
   KeyPreview      =   -1  'True
   LinkTopic       =   "Form1"
   LockControls    =   -1  'True
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   600
   ScaleMode       =   3  'Pixel
   ScaleWidth      =   800
   StartUpPosition =   2  'CenterScreen
   Begin VB.CommandButton cmdClose 
      Caption         =   "&Close"
      Height          =   375
      Left            =   10560
      TabIndex        =   20
      Top             =   8520
      Width           =   1335
   End
   Begin VB.CommandButton cmdRefresh 
      Caption         =   "&Refresh"
      Height          =   375
      Left            =   9120
      TabIndex        =   19
      Top             =   8520
      Width           =   1335
   End
   Begin VB.Frame fraGrids 
      Caption         =   "Details"
      Height          =   4215
      Left            =   120
      TabIndex        =   14
      Top             =   4800
      Width           =   11775
      Begin MSFlexGridLib.MSFlexGrid grdTopInv 
         Height          =   3855
         Left            =   6000
         TabIndex        =   16
         Top             =   240
         Width           =   5655
         _ExtentX        =   9975
         _ExtentY        =   6800
         _Version        =   393216
         Cols            =   4
         FixedCols       =   0
      End
      Begin MSFlexGridLib.MSFlexGrid grdDayWise 
         Height          =   3855
         Left            =   120
         TabIndex        =   15
         Top             =   240
         Width           =   5775
         _ExtentX        =   10186
         _ExtentY        =   6800
         _Version        =   393216
         Cols            =   5
         FixedCols       =   0
      End
      Begin VB.Label lblTopInvTitle 
         Caption         =   "Top 10 Invoices"
         Height          =   255
         Left            =   6000
         TabIndex        =   18
         Top             =   0
         Width           =   5655
      End
      Begin VB.Label lblDayTitle 
         Caption         =   "Day-wise Sales"
         Height          =   255
         Left            =   120
         TabIndex        =   17
         Top             =   0
         Width           =   5775
      End
   End
   Begin VB.Frame fraKpi 
      Caption         =   "Summary (current period vs last month)"
      Height          =   2520
      Left            =   120
      TabIndex        =   1
      Top             =   1920
      Width           =   11775
      Begin VB.Label lblCmpAvg 
         Alignment       =   2  'Center
         Caption         =   "-"
         ForeColor       =   &H00808080&
         Height          =   495
         Left            =   9480
         TabIndex        =   13
         Top             =   1920
         Width           =   2175
      End
      Begin VB.Label lblCmpPct 
         Alignment       =   2  'Center
         Caption         =   "-"
         ForeColor       =   &H00808080&
         Height          =   495
         Left            =   7200
         TabIndex        =   12
         Top             =   1920
         Width           =   2175
      End
      Begin VB.Label lblCmpProfit 
         Alignment       =   2  'Center
         Caption         =   "-"
         ForeColor       =   &H00808080&
         Height          =   495
         Left            =   4920
         TabIndex        =   11
         Top             =   1920
         Width           =   2175
      End
      Begin VB.Label lblCmpCost 
         Alignment       =   2  'Center
         Caption         =   "-"
         ForeColor       =   &H00808080&
         Height          =   495
         Left            =   2520
         TabIndex        =   10
         Top             =   1920
         Width           =   2295
      End
      Begin VB.Label lblCmpSale 
         Alignment       =   2  'Center
         Caption         =   "-"
         ForeColor       =   &H00808080&
         Height          =   495
         Left            =   240
         TabIndex        =   9
         Top             =   1920
         Width           =   2175
      End
      Begin VB.Label lblAvgSale 
         Alignment       =   2  'Center
         Caption         =   "0"
         BeginProperty Font 
            Name            =   "Verdana"
            Size            =   12
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   375
         Left            =   9480
         TabIndex        =   8
         Top             =   1080
         Width           =   2175
      End
      Begin VB.Label lblProfitPct 
         Alignment       =   2  'Center
         Caption         =   "0"
         BeginProperty Font 
            Name            =   "Verdana"
            Size            =   12
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   375
         Left            =   7200
         TabIndex        =   7
         Top             =   1080
         Width           =   2175
      End
      Begin VB.Label lblProfit 
         Alignment       =   2  'Center
         Caption         =   "0"
         BeginProperty Font 
            Name            =   "Verdana"
            Size            =   12
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00008000&
         Height          =   375
         Left            =   4920
         TabIndex        =   6
         Top             =   1080
         Width           =   2175
      End
      Begin VB.Label lblTotalCost 
         Alignment       =   2  'Center
         Caption         =   "0"
         BeginProperty Font 
            Name            =   "Verdana"
            Size            =   12
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   375
         Left            =   2520
         TabIndex        =   5
         Top             =   1080
         Width           =   2295
      End
      Begin VB.Label lblTotalSale 
         Alignment       =   2  'Center
         Caption         =   "0"
         BeginProperty Font 
            Name            =   "Verdana"
            Size            =   12
            Charset         =   0
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00C00000&
         Height          =   375
         Left            =   240
         TabIndex        =   4
         Top             =   1080
         Width           =   2175
      End
      Begin VB.Label lblKpiAvg 
         Alignment       =   2  'Center
         Caption         =   "Avg Sale / Day"
         Height          =   255
         Left            =   9480
         TabIndex        =   3
         Top             =   720
         Width           =   2175
      End
      Begin VB.Label lblKpiPct 
         Alignment       =   2  'Center
         Caption         =   "Profit %"
         Height          =   255
         Left            =   7200
         TabIndex        =   2
         Top             =   720
         Width           =   2175
      End
      Begin VB.Label lblKpiProfit 
         Alignment       =   2  'Center
         Caption         =   "Profit"
         Height          =   255
         Left            =   4920
         TabIndex        =   22
         Top             =   720
         Width           =   2175
      End
      Begin VB.Label lblKpiCost 
         Alignment       =   2  'Center
         Caption         =   "Total Cost"
         Height          =   255
         Left            =   2520
         TabIndex        =   0
         Top             =   720
         Width           =   2295
      End
      Begin VB.Label lblKpiSale 
         Alignment       =   2  'Center
         Caption         =   "Total Sale"
         Height          =   255
         Left            =   240
         TabIndex        =   23
         Top             =   720
         Width           =   2175
      End
   End
   Begin VB.Frame fraFilter 
      Caption         =   "Date Range (business day 08:00 to next day 05:00)"
      Height          =   1695
      Left            =   120
      TabIndex        =   24
      Top             =   120
      Width           =   11775
      Begin VB.CommandButton cmdLast30 
         Caption         =   "Last 30 Days"
         Height          =   315
         Left            =   10320
         TabIndex        =   25
         Top             =   1200
         Width           =   1335
      End
      Begin VB.CommandButton cmdLast7 
         Caption         =   "Last 7 Days"
         Height          =   315
         Left            =   8880
         TabIndex        =   26
         Top             =   1200
         Width           =   1335
      End
      Begin VB.CommandButton cmdLastMonth 
         Caption         =   "Last Month"
         Height          =   315
         Left            =   7440
         TabIndex        =   27
         Top             =   1200
         Width           =   1335
      End
      Begin VB.CommandButton cmdThisMonth 
         Caption         =   "This Month"
         Height          =   315
         Left            =   6000
         TabIndex        =   28
         Top             =   1200
         Width           =   1335
      End
      Begin VB.CommandButton cmdYesterday 
         Caption         =   "Yesterday"
         Height          =   315
         Left            =   4560
         TabIndex        =   29
         Top             =   1200
         Width           =   1335
      End
      Begin VB.CommandButton cmdToday 
         Caption         =   "Today"
         Height          =   315
         Left            =   3120
         TabIndex        =   30
         Top             =   1200
         Width           =   1335
      End
      Begin MSComCtl2.DTPicker dtpTo 
         Height          =   360
         Left            =   6120
         TabIndex        =   31
         Top             =   600
         Width           =   2775
         _ExtentX        =   4895
         _ExtentY        =   635
         _Version        =   393216
         CustomFormat    =   "dd-MMM-yyyy HH:mm"
         Format          =   137101315
         CurrentDate     =   45658
      End
      Begin MSComCtl2.DTPicker dtpFrom 
         Height          =   360
         Left            =   960
         TabIndex        =   32
         Top             =   600
         Width           =   2775
         _ExtentX        =   4895
         _ExtentY        =   635
         _Version        =   393216
         CustomFormat    =   "dd-MMM-yyyy HH:mm"
         Format          =   137101315
         CurrentDate     =   45658
      End
      Begin VB.Label lblTo 
         Caption         =   "To"
         Height          =   255
         Left            =   5520
         TabIndex        =   33
         Top             =   660
         Width           =   495
      End
      Begin VB.Label lblFrom 
         Caption         =   "From"
         Height          =   255
         Left            =   240
         TabIndex        =   34
         Top             =   660
         Width           =   615
      End
   End
   Begin VB.Label lblComparePeriod 
      Caption         =   "Last month: -"
      ForeColor       =   &H00808080&
      Height          =   255
      Left            =   240
      TabIndex        =   22
      Top             =   4290
      Width           =   11535
   End
   Begin VB.Label lblPeriod 
      Caption         =   "Current: -"
      Height          =   255
      Left            =   240
      TabIndex        =   21
      Top             =   4530
      Width           =   11535
   End
End
Attribute VB_Name = "FrmSalesDashboard"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Const BIZ_START_HOUR As Integer = 8
Private Const BIZ_END_HOUR As Integer = 5

Private Type SalesSummary
    TotalSale As Double
    TotalCost As Double
    Profit As Double
    ProfitPct As Variant
    AvgSale As Double
    totalDays As Long
End Type

Private Sub Form_Load()
    SetupGrids
    ApplyPreset "this-month"
End Sub

Private Sub cmdClose_Click()
    Unload Me
End Sub

Private Sub cmdRefresh_Click()
    LoadDashboard
End Sub

Private Sub cmdToday_Click()
    ApplyPreset "today"
End Sub

Private Sub cmdYesterday_Click()
    ApplyPreset "yesterday"
End Sub

Private Sub cmdThisMonth_Click()
    ApplyPreset "this-month"
End Sub

Private Sub cmdLastMonth_Click()
    ApplyPreset "last-month"
End Sub

Private Sub cmdLast7_Click()
    ApplyPreset "last-7"
End Sub

Private Sub cmdLast30_Click()
    ApplyPreset "last-30"
End Sub

Private Sub SetupGrids()
    With grdDayWise
        .Clear
        .Rows = 2
        .Cols = 5
        .FixedRows = 1
        .Row = 0
        .Col = 0: .Text = "Business Day"
        .Col = 1: .Text = "Total Sale"
        .Col = 2: .Text = "Total Cost"
        .Col = 3: .Text = "Profit"
        .Col = 4: .Text = "Invoices"
        .ColWidth(0) = 2200
        .ColWidth(1) = 1300
        .ColWidth(2) = 1300
        .ColWidth(3) = 1300
        .ColWidth(4) = 900
    End With

    With grdTopInv
        .Clear
        .Rows = 2
        .Cols = 4
        .FixedRows = 1
        .Row = 0
        .Col = 0: .Text = "Invoice #"
        .Col = 1: .Text = "Total Sale"
        .Col = 2: .Text = "Qty"
        .Col = 3: .Text = "Discount"
        .ColWidth(0) = 1200
        .ColWidth(1) = 1500
        .ColWidth(2) = 1000
        .ColWidth(3) = 1200
    End With
End Sub

Private Sub ApplyPreset(ByVal preset As String)
    Dim nowDt As Date
    Dim bd As Date
    Dim Y As Integer
    Dim m As Integer
    Dim lastD As Date

    nowDt = Now
    preset = LCase$(Trim$(preset))

    Select Case preset
        Case "today"
            bd = BusinessDateFor(nowDt)
            dtpFrom.Value = BusinessDayStart(bd)
            dtpTo.Value = nowDt

        Case "yesterday"
            bd = BusinessDateFor(nowDt)
            bd = DateAdd("d", -1, bd)
            dtpFrom.Value = BusinessDayStart(bd)
            dtpTo.Value = BusinessDayEnd(bd)

        Case "last-month"
            If Month(nowDt) = 1 Then
                Y = Year(nowDt) - 1: m = 12
            Else
                Y = Year(nowDt): m = Month(nowDt) - 1
            End If
            lastD = DateSerial(Y, m + 1, 0)
            dtpFrom.Value = BusinessDayStart(DateSerial(Y, m, 1))
            dtpTo.Value = BusinessDayEnd(lastD)

        Case "last-7"
            bd = BusinessDateFor(nowDt)
            dtpFrom.Value = BusinessDayStart(DateAdd("d", -6, bd))
            dtpTo.Value = nowDt

        Case "last-30"
            bd = BusinessDateFor(nowDt)
            dtpFrom.Value = BusinessDayStart(DateAdd("d", -29, bd))
            dtpTo.Value = nowDt

        Case Else  ' this-month
            dtpFrom.Value = BusinessDayStart(DateSerial(Year(nowDt), Month(nowDt), 1))
            dtpTo.Value = nowDt
    End Select

    LoadDashboard
End Sub

Private Sub LoadDashboard()
On Error GoTo Err_Handler

    Dim cur As SalesSummary
    Dim prev As SalesSummary
    Dim prevFrom As Date
    Dim prevTo As Date

    Screen.MousePointer = vbHourglass
    lblPeriod.Caption = "Current: " & Format(dtpFrom.Value, "dd-mmm-yyyy hh:nn") & _
        "  to  " & Format(dtpTo.Value, "dd-mmm-yyyy hh:nn")

    cur = FetchSummary(dtpFrom.Value, dtpTo.Value)
    ShiftPreviousPeriod dtpFrom.Value, dtpTo.Value, prevFrom, prevTo
    prev = FetchSummary(prevFrom, prevTo)

    lblComparePeriod.Caption = "Last month: " & Format(prevFrom, "dd-mmm-yyyy hh:nn") & _
        "  to  " & Format(prevTo, "dd-mmm-yyyy hh:nn")

    lblTotalSale.Caption = FormatMoney(cur.TotalSale)
    lblTotalCost.Caption = FormatMoney(cur.TotalCost)
    lblProfit.Caption = FormatMoney(cur.Profit)
    If IsNull(cur.ProfitPct) Then
        lblProfitPct.Caption = "-"
    Else
        lblProfitPct.Caption = Format(cur.ProfitPct, "0.00") & "%"
    End If
    lblAvgSale.Caption = FormatMoney(cur.AvgSale)

    lblCmpSale.Caption = FormatCompare(cur.TotalSale, prev.TotalSale)
    lblCmpCost.Caption = FormatCompare(cur.TotalCost, prev.TotalCost)
    lblCmpProfit.Caption = FormatCompare(cur.Profit, prev.Profit)
    lblCmpPct.Caption = FormatComparePct(cur.ProfitPct, prev.ProfitPct)
    lblCmpAvg.Caption = FormatCompare(cur.AvgSale, prev.AvgSale)

    LoadDayWiseGrid dtpFrom.Value, dtpTo.Value
    LoadTopInvoicesGrid dtpFrom.Value, dtpTo.Value

    Screen.MousePointer = vbDefault
    Exit Sub

Err_Handler:
    Screen.MousePointer = vbDefault
    MsgBox "Sales Dashboard error:" & vbCrLf & Err.Description, vbExclamation, "Sales Dashboard"
End Sub

Private Function FetchSummary(ByVal dtFrom As Date, ByVal dtTo As Date) As SalesSummary
    Dim SQL As String
    Dim Rs As ADODB.Recordset
    Dim totalDays As Long

    totalDays = CountBusinessDays(dtFrom, dtTo)
    If totalDays < 1 Then totalDays = 1

    SQL = "SELECT " & _
          "SUM(TOTAL_AMT) AS total_sale, " & _
          "SUM(COST_AMT * QTY) AS total_cost, " & _
          "SUM(TOTAL_AMT) - SUM(COST_AMT * QTY) AS profit, " & _
          "CASE WHEN SUM(COST_AMT * QTY) = 0 THEN NULL " & _
          "ELSE (SUM(TOTAL_AMT) - SUM(COST_AMT * QTY)) / SUM(COST_AMT * QTY) * 100 END AS profit_pct, " & _
          "SUM(TOTAL_AMT) / " & totalDays & " AS avg_sale " & _
          "FROM V_FIN_SALE_DISC_NEW2 " & _
          "WHERE INV_ID BETWEEN 1 AND 999999999 " & _
          "AND DOC_DATE_T BETWEEN '" & SqlDateTime(dtFrom) & "' AND '" & SqlDateTime(dtTo) & "'"

    Set Rs = FetchAll(SQL)
    With Rs
        If Not .EOF Then
            FetchSummary.TotalSale = NzDbl(!total_sale)
            FetchSummary.TotalCost = NzDbl(!total_cost)
            FetchSummary.Profit = NzDbl(!profit)
            FetchSummary.ProfitPct = !profit_pct
            FetchSummary.AvgSale = NzDbl(!avg_sale)
        End If
        .Close
    End With
    FetchSummary.totalDays = totalDays
    Set Rs = Nothing
End Function

Private Sub LoadDayWiseGrid(ByVal dtFrom As Date, ByVal dtTo As Date)
    Dim SQL As String
    Dim Rs As ADODB.Recordset
    Dim r As Long

    SQL = "SELECT " & BizDateExpr("DOC_DATE_T") & " AS biz_date, " & _
          "SUM(TOTAL_AMT) AS total_sale, " & _
          "SUM(COST_AMT * QTY) AS total_cost, " & _
          "SUM(TOTAL_AMT) - SUM(COST_AMT * QTY) AS profit, " & _
          "COUNT(DISTINCT INV_ID) AS inv_count " & _
          "FROM V_FIN_SALE_DISC_NEW2 " & _
          "WHERE INV_ID BETWEEN 1 AND 999999999 " & _
          "AND DOC_DATE_T BETWEEN '" & SqlDateTime(dtFrom) & "' AND '" & SqlDateTime(dtTo) & "' " & _
          "GROUP BY " & BizDateExpr("DOC_DATE_T") & " " & _
          "ORDER BY biz_date DESC"

    Set Rs = FetchAll(SQL)
    grdDayWise.Rows = 1
    r = 1
    Do While Not Rs.EOF
        grdDayWise.Rows = grdDayWise.Rows + 1
        grdDayWise.Row = r
        grdDayWise.Col = 0: grdDayWise.Text = Format(Rs!biz_date, "dd-mmm-yyyy")
        grdDayWise.Col = 1: grdDayWise.Text = FormatMoney(NzDbl(Rs!total_sale))
        grdDayWise.Col = 2: grdDayWise.Text = FormatMoney(NzDbl(Rs!total_cost))
        grdDayWise.Col = 3: grdDayWise.Text = FormatMoney(NzDbl(Rs!profit))
        grdDayWise.Col = 4: grdDayWise.Text = Format(NzLng(Rs!inv_count), "#,##0")
        r = r + 1
        Rs.MoveNext
    Loop
    Rs.Close
    Set Rs = Nothing
End Sub

Private Sub LoadTopInvoicesGrid(ByVal dtFrom As Date, ByVal dtTo As Date)
    Dim SQL As String
    Dim Rs As ADODB.Recordset
    Dim r As Long

    SQL = "SELECT TOP 10 INV_ID AS inv_id, " & _
          "SUM(TOTAL_AMT) AS total_sale, " & _
          "SUM(QTY) AS total_qty, " & _
          "SUM(DISC_AMT) AS total_disc " & _
          "FROM V_FIN_SALE_DISC_NEW2 " & _
          "WHERE INV_ID BETWEEN 1 AND 999999999 " & _
          "AND DOC_DATE_T BETWEEN '" & SqlDateTime(dtFrom) & "' AND '" & SqlDateTime(dtTo) & "' " & _
          "GROUP BY INV_ID " & _
          "ORDER BY SUM(TOTAL_AMT) DESC"

    Set Rs = FetchAll(SQL)
    grdTopInv.Rows = 1
    r = 1
    Do While Not Rs.EOF
        grdTopInv.Rows = grdTopInv.Rows + 1
        grdTopInv.Row = r
        grdTopInv.Col = 0: grdTopInv.Text = Format(NzLng(Rs!Inv_id), "#,##0")
        grdTopInv.Col = 1: grdTopInv.Text = FormatMoney(NzDbl(Rs!total_sale))
        grdTopInv.Col = 2: grdTopInv.Text = Format(NzDbl(Rs!Total_Qty), "#,##0.##")
        grdTopInv.Col = 3: grdTopInv.Text = FormatMoney(NzDbl(Rs!total_disc))
        r = r + 1
        Rs.MoveNext
    Loop
    Rs.Close
    Set Rs = Nothing
End Sub

Private Function BizDateExpr(ByVal colName As String) As String
    BizDateExpr = "CASE WHEN DATEPART(hour, " & colName & ") < " & BIZ_START_HOUR & _
                  " THEN DATEADD(day, -1, CAST(" & colName & " AS DATE)) " & _
                  "ELSE CAST(" & colName & " AS DATE) END"
End Function

Private Function BusinessDateFor(ByVal dt As Date) As Date
    If Hour(dt) < BIZ_START_HOUR Then
        BusinessDateFor = DateAdd("d", -1, DateValue(dt))
    Else
        BusinessDateFor = DateValue(dt)
    End If
End Function

Private Function BusinessDayStart(ByVal d As Date) As Date
    BusinessDayStart = DateSerial(Year(d), Month(d), Day(d)) + TimeSerial(BIZ_START_HOUR, 0, 0)
End Function

Private Function BusinessDayEnd(ByVal d As Date) As Date
    BusinessDayEnd = DateAdd("d", 1, DateSerial(Year(d), Month(d), Day(d))) + TimeSerial(BIZ_END_HOUR, 0, 0)
End Function

Private Function CountBusinessDays(ByVal dtFrom As Date, ByVal dtTo As Date) As Long
    Dim firstBd As Date
    Dim lastBd As Date
    firstBd = BusinessDateFor(dtFrom)
    lastBd = BusinessDateFor(dtTo)
    CountBusinessDays = DateDiff("d", firstBd, lastBd) + 1
    If CountBusinessDays < 1 Then CountBusinessDays = 1
End Function

Private Sub ShiftPreviousPeriod(ByVal dtFrom As Date, ByVal dtTo As Date, ByRef prevFrom As Date, ByRef prevTo As Date)
    Dim startBd As Date
    Dim endBd As Date
    Dim prevStartBd As Date
    Dim prevLast As Date

    startBd = BusinessDateFor(dtFrom)
    endBd = BusinessDateFor(dtTo)
    prevStartBd = ShiftDateMonths(startBd, -1)
    prevFrom = BusinessDayStart(prevStartBd)

    If IsFullCalendarMonthPeriod(startBd, endBd, dtTo) Then
        prevLast = LastCalendarDay(Year(prevStartBd), Month(prevStartBd))
        prevTo = BusinessDayEnd(prevLast)
        Exit Sub
    End If

    If IsBusinessDayClose(dtTo) Then
        prevTo = BusinessDayEnd(ShiftDateMonths(endBd, -1))
        If prevTo <= prevFrom Then prevTo = BusinessDayEnd(prevStartBd)
        Exit Sub
    End If

    If IsMonthEndPartial(endBd, dtTo) Then
        prevLast = LastCalendarDay(Year(prevStartBd), Month(prevStartBd))
        prevTo = BusinessDayEnd(prevLast)
        Exit Sub
    End If

    prevTo = DateAdd("m", -1, dtTo)
    If prevTo <= prevFrom Then
        prevTo = BusinessDayEnd(ShiftDateMonths(endBd, -1))
    End If
End Sub

Private Function LastCalendarDay(ByVal Y As Integer, ByVal m As Integer) As Date
    LastCalendarDay = DateSerial(Y, m + 1, 0)
End Function

Private Function ShiftDateMonths(ByVal d As Date, ByVal months As Integer) As Date
    Dim mi As Long
    Dim Y As Integer
    Dim mo As Integer
    Dim dy As Integer
    mi = (Month(d) - 1) + months
    Y = Year(d) + (mi \ 12)
    mo = (mi Mod 12) + 1
    dy = Day(d)
    If dy > Day(LastCalendarDay(Y, mo)) Then dy = Day(LastCalendarDay(Y, mo))
    ShiftDateMonths = DateSerial(Y, mo, dy)
End Function

Private Function IsBusinessDayClose(ByVal dt As Date) As Boolean
    IsBusinessDayClose = (Hour(dt) < BIZ_START_HOUR)
End Function

Private Function IsFullCalendarMonthPeriod(ByVal startBd As Date, ByVal endBd As Date, ByVal dtEnd As Date) As Boolean
    If Day(startBd) <> 1 Then Exit Function
    If Month(startBd) <> Month(endBd) Or Year(startBd) <> Year(endBd) Then Exit Function
    If Not IsBusinessDayClose(dtEnd) Then Exit Function
    IsFullCalendarMonthPeriod = (endBd = LastCalendarDay(Year(endBd), Month(endBd)))
End Function

Private Function IsMonthEndPartial(ByVal endBd As Date, ByVal dtEnd As Date) As Boolean
    If endBd <> LastCalendarDay(Year(endBd), Month(endBd)) Then Exit Function
    IsMonthEndPartial = (Hour(dtEnd) >= BIZ_START_HOUR And Not IsBusinessDayClose(dtEnd))
End Function

Private Function SqlDateTime(ByVal dt As Date) As String
    SqlDateTime = Format(Year(dt), "0000") & "-" & Format(Month(dt), "00") & "-" & Format(Day(dt), "00") & " " & _
                  Format(Hour(dt), "00") & ":" & Format(Minute(dt), "00") & ":" & Format(Second(dt), "00")
End Function

Private Function FormatMoney(ByVal v As Double) As String
    FormatMoney = Format(v, "#,##0")
End Function

Private Function FormatCompare(ByVal current As Double, ByVal previous As Double) As String
    Dim s As String
    s = "Last month: " & FormatMoney(previous)
    If previous = 0 Then
        FormatCompare = s & vbCrLf & "- % vs prev"
    Else
        FormatCompare = s & vbCrLf & Format((current - previous) / previous * 100, "+0.0;-0.0") & "% vs prev"
    End If
End Function

Private Function FormatComparePct(ByVal current As Variant, ByVal previous As Variant) As String
    Dim s As String
    If IsNull(previous) Then
        s = "Last month: -"
    Else
        s = "Last month: " & Format(CDbl(previous), "0.00") & "%"
    End If
    If IsNull(current) Or IsNull(previous) Then
        FormatComparePct = s & vbCrLf & "- pts"
    Else
        FormatComparePct = s & vbCrLf & Format(CDbl(current) - CDbl(previous), "+0.00;-0.00") & " pts"
    End If
End Function

Private Function NzDbl(ByVal v As Variant) As Double
    If IsNull(v) Then
        NzDbl = 0
    Else
        NzDbl = CDbl(v)
    End If
End Function

Private Function NzLng(ByVal v As Variant) As Long
    If IsNull(v) Then
        NzLng = 0
    Else
        NzLng = CLng(v)
    End If
End Function

