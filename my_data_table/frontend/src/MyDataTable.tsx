import React, { useState, useEffect, ReactText } from "react"
import { range, zipObject } from "lodash"
import { 
  RowDetailState,
  IntegratedSummary,
  Column,
  GroupRow,
  SummaryState,
  DataTypeProvider,
  DataTypeProviderProps,
} from "@devexpress/dx-react-grid"
import {
  Grid,
  Table,
  VirtualTable,
  TableHeaderRow,
  TableRowDetail,
  TableSummaryRow,
  TableColumnVisibility,
} from "@devexpress/dx-react-grid-material-ui"
import {
  ArrowTable,
  ComponentProps,
  Streamlit,
  withStreamlitConnection,
} from "streamlit-component-lib"
import { table } from "console"

interface TableRowsProps {
  isHeader: boolean
  table: ArrowTable
}

const CurrencyFormatter = ( props: DataTypeProvider.ValueFormatterProps) => {
  const {value} = props;
  if (value==0) {
    return (<b></b>)
  } else {
  return (
    <b style={{ color: 'darkblue' }}>
    {value.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' })}
    </b>
  )
  }
};
const CurrencyTypeProvider = (props: DataTypeProviderProps) => (
  <DataTypeProvider
    formatterComponent={CurrencyFormatter}
    {...props}
  />
);

const RowDetail = (props: TableRowDetail.ContentProps) => {
  const { row } = props;
  const  detCols = [
    { name: "Fecha"},
    { name: "Producto"}, 
    { name: "Costo",title:"P. Unitario"},
    { name: "Cant",title:"Cantidad"},
    { name: "Unid", title: "Unidad"},
    { name: "Total",title: "Precio"},
  ]
  const colExt:Table.ColumnExtension[] = [
    {columnName:"Cant", align:"center", width:"80px"},
    {columnName:"Costo", align:"right", width:"100px"},
    {columnName:"Unid",  width:"70px"}, 
    {columnName:"Total", align:"right", width:"100px"},
    
  ]
  if (row.Invoice==null)
  {
    return (<span>{row.Detalle}</span>)
  }
  return (
  <div>
    <Grid rows={row.details} columns={detCols}>
      <Table columnExtensions={colExt}/>
      <CurrencyTypeProvider for={["Costo","Total"]}/>
      <TableHeaderRow/>
    </Grid>
  </div>
  )
};
/**
 * Function returning a list of rows.
 *
 * isHeader     - Whether to display the header.
 * table        - The table to display.
 */
const tableRows = (props: TableRowsProps): any[][] => {
  const { isHeader, table } = props
  const { headerRows, rows } = table
  const startRow = isHeader ? 0 : headerRows
  const endRow = isHeader ? headerRows : rows

  const tableRows = range(startRow, endRow).map(rowIndex =>
    tableRow({ rowIndex, table })
  )

  return tableRows
}

interface TableRowProps {
  rowIndex: number
  table: ArrowTable
}

/**
 * Function returning a list entries for a row.
 *
 * rowIndex - The row index.
 * table    - The table to display.
 */
const tableRow = (props: TableRowProps): any[] => {
  const { rowIndex, table } = props
  const { columns } = table

  const cells = range(0, columns).map(columnIndex => {
    const { content } = table.getCell(rowIndex, columnIndex)
    if (typeof content ==="bigint")
      return Number(content)
    return (content)
  })

  return cells
}

const formatRows = (rows: any[][], columns: string[][], details: any) => {
  return rows.map(row => {
    var fila = zipObject(columns[0], row)
    fila["details"]=details[fila.Invoice]
    return fila
  })  
}

const formatColumns = (columns: string[][]) =>
  columns[0].map(column => ({ name: column }))

const MyDataTable: React.FC<ComponentProps> = props => {
  useEffect(() => {
    Streamlit.setFrameHeight(800)
  })

  const columns = tableRows({ isHeader: true, table: props.args.data})
  const rows = tableRows({ isHeader: false, table: props.args.data })
  
  const tableColumnExtensions: Table.ColumnExtension[] = [
    { columnName: 'Cargo', align: "right" },
    { columnName: 'Abono', align: "right" },
    { columnName: 'Descripción', width:"250px", wordWrapEnabled: true},
  ];
  const [currencyColumns] = useState(['Cargo','Abono']);
  const [totalSummaryItems] = useState([
    { columnName: 'Cargo', type: 'sum' },
    { columnName: 'Abono', type: 'sum' }, 
  ]);
  const [defaultHiddenColumnNames] = useState([
    'Rut',
    'Invoice',
    'Socio',
    'index',
    '',
    'level_0',
    'Detalle'
  ]);
  const realRows = formatRows(rows,columns,props.args.details);
  const realColumns = formatColumns(columns);
  console.log(realRows)
  return (
    <Grid rows={realRows} columns={realColumns}>
      <CurrencyTypeProvider for={currencyColumns}/>
      <SummaryState
        totalItems={totalSummaryItems}/>
        <RowDetailState/>
      <IntegratedSummary/>
      <VirtualTable columnExtensions={tableColumnExtensions}/>
      <TableColumnVisibility
          defaultHiddenColumnNames={defaultHiddenColumnNames}
      />
      <TableHeaderRow/>
      <TableRowDetail contentComponent={RowDetail}/>
      <TableSummaryRow/>
    </Grid>
  )
}

export default withStreamlitConnection(MyDataTable)
