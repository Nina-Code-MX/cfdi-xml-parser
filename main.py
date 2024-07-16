import os
import xml.etree.ElementTree as ET
import csv

c_Impuesto = {
    "002": "IVA",
    "003": "IEPS"
}

c_ImpuestoRetenido = {
    "001": "ISR",
    "002": "IVA",
    "003": "IEPS"
}

c_TipoDeduccion = {
    "002": "ISR",
}

c_TipoDeduccionImss = {
    "001": "Seguridad social",
    "003": "Aportaciones a retiro, cesantía en edad avanzada y vejez.",
    "005": "Aportaciones a Fondo de vivienda",
    "006": "Descuento por incapacidad Sumatoria de los valores de los atributos Descuento del nodo Incapacidad",
    "007": "Pensión alimenticia",
    "009": "Préstamos provenientes del Fondo Nacional de la Vivienda para los Trabajadores",
    "010": "Pago por crédito de vivienda",
    "011": "Pago de abonos INFONACOT",
    "021": "Cuotas obrero patronales"
}

c_TipoDeduccionOtros = {
    "004": "Otros",
    "008": "Renta",
    "012": "Anticipo de salarios",
    "013": "Pagos hechos con exceso al trabajador",
    "014": "Errores",
    "015": "Pérdidas",
    "016": "Averías",
    "017": "Adquisición de artículos producidos por la empresa o establecimiento",
    "018": "Cuotas para la constitución y fomento de sociedades cooperativas y de cajas de ahorro",
    "019": "Cuotas sindicales",
    "020": "Ausencia (Ausentismo)",
    "021": "Cuotas obrero patronales"
}

def parse_xml_to_csv(input_folder, output_csv_filename="report.csv"):
    header = ["Fecha", "Emisor Rfc", "Emisor Nombre", "Receptor Rfc", "Receptor Nombre", "Moneda", "TipoCambio", "SubTotal", "Descuento", "Traslado: I.V.A.", "Traslado: I.E.P.S", "Retención: I.S.R.", "Retención: I.V.A.", "Retención: I.E.P.S", "Deducción: I.S.R.", "Deducción: I.M.S.S.", "Deducción: Otros", "Total", "Ingreso/Egreso", "Tipo de Comprobante", "Folio SAT"]

    with open(output_csv_filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)

        for filename in os.listdir(input_folder):
            if filename.endswith(".xml"):
                tree = ET.parse(os.path.join(input_folder, filename))
                root = tree.getroot()

                ns = {
                    'cfdi':'http://www.sat.gob.mx/cfd/4',
                    'nomina12':'http://www.sat.gob.mx/nomina12',
                    'tfd':'http://www.sat.gob.mx/TimbreFiscalDigital',
                }
                comprobante = root
                emisor = comprobante.find("cfdi:Emisor", ns)
                receptor = comprobante.find("cfdi:Receptor", ns)
                impuestosRoot = comprobante.find("cfdi:Impuestos", ns)
                complementoRoot = comprobante.find("cfdi:Complemento", ns)
                folio_sat = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"

                impuestos_traslados = {
                    "IVA": 0.00,
                    "IEPS": 0.00
                }

                impuestos_retenidos = {
                    "ISR": 0.00,
                    "IVA": 0.00,
                    "IEPS": 0.00
                }

                impuestos_deducidos = {
                    "ISR": 0.00,
                    "IMSS": 0.00,
                    "OTROS": 0.00
                }

                if impuestosRoot is not None:
                    traslados = impuestosRoot.findall(".//cfdi:Traslado", ns)
                    retenciones = impuestosRoot.findall(".//cfdi:Retencion", ns)

                    for traslado in traslados:
                        impuesto = traslado.get("Impuesto")
                        importe = float(traslado.get("Importe", 0.00))

                        if impuesto in c_Impuesto:
                            if impuesto == "002":
                                impuestos_traslados["IVA"] += importe
                            
                            if impuesto == "003":
                                impuestos_traslados["IEPS"] += importe

                    for retencion in retenciones:
                        impuesto = retencion.get("Impuesto")
                        importe = float(retencion.get("Importe", 0.00))

                        if impuesto in c_ImpuestoRetenido:
                            if impuesto == "001":
                                impuestos_retenidos["ISR"] += importe

                            if impuesto == "002":
                                impuestos_retenidos["IVA"] += importe

                            if impuesto == "003":
                                impuestos_retenidos["IEPS"] += importe

                if complementoRoot is not None:
                    deducciones = complementoRoot.findall(".//nomina12:Deduccion", ns)
                    timbrefiscaldigital = complementoRoot.find(".//tfd:TimbreFiscalDigital", ns)
                    folio_sat = timbrefiscaldigital.get("UUID").upper()

                    for deduccion in deducciones:
                        impuesto = deduccion.get("TipoDeduccion")
                        importe = float(deduccion.get("Importe", "0.00"))

                        if impuesto in c_TipoDeduccionImss:
                            impuestos_deducidos["IMSS"] += importe

                        if impuesto in c_TipoDeduccionOtros:
                            impuestos_deducidos["OTROS"] += importe

                        if impuesto in c_TipoDeduccion:
                            impuestos_deducidos["ISR"] += importe

                tipoCambio = float(comprobante.get("TipoCambio", "1.00")) if comprobante.get("TipoCambio", "1.00") else 1.00
                total = float(comprobante.get("Total", "0.00")) if comprobante.get("Total", "0.00") else 0.00

                row = [
                    comprobante.get("Fecha"),
                    emisor.get("Rfc"),
                    emisor.get("Nombre"),
                    receptor.get("Rfc"),
                    receptor.get("Nombre"),
                    comprobante.get("Moneda", "MXN"),
                    tipoCambio,
                    comprobante.get("SubTotal", "0.00"),
                    comprobante.get("Descuento", "0.00")
                ]

                for traslado in impuestos_traslados.values():
                    row.append(traslado)

                for retencion in impuestos_retenidos.values():
                    row.append(retencion)

                for deduccion in impuestos_deducidos.values():
                    row.append(deduccion)

                row += [
                    total,
                    total * tipoCambio,
                    comprobante.get("TipoDeComprobante"),
                    folio_sat
                ]

                writer.writerow(row)

if __name__ == "__main__":
    input_folder = input("Enter the path to the folder containing the XML files: ").strip('"') or "/Users/germannoegonzalez/Library/CloudStorage/OneDrive-FICO/Desktop/AllFacturas"
    output_csv_filename = input("Enter the name of the output CSV file: ") or "report.csv"
    parse_xml_to_csv(input_folder, output_csv_filename)
