import requests
import pandas as pd
from datetime import datetime

URL = "http://172.16.176.40/csquery.php?act=dose&list=results_time"


class Data:

    def __init__(self):
        self.data = None

    def fetch(self):
        try:
            resp = requests.get(URL, timeout=3).text
        except requests.exceptions.RequestException as e:
            print("Error: ", e)
            return

        raw_data = resp.split("<pre>")[1].split("</pre>")[0]
        self.data = raw_data

    def column_widths(self, length_determining_line) -> list[int]:
        # grab line like ..=== ==== ================ == = ... and get the lengths of the columns
        equal_signs_list = length_determining_line.split(" ")
        widths = [len(width) for width in equal_signs_list if width]
        return widths

    def get_row_data(self, row: str, column_widths: list[int]) -> list:
        value_start = 0
        value_end = 0
        values = []
        for wdt in column_widths:
            value_end = value_start + wdt + 1
            value = row[value_start:value_end].strip()
            values.append(value)
            value_start = value_end
        return values

    # def get_column_names(self) -> list:
    #     column_line = self.data.split("\n")[5]
    #     print(self.get_row_data(column_line))

    def get_dataframe(self) -> pd.DataFrame:
        lines = self.data.split("\n")
        length_determining_line = lines[6]
        column_widths = list(self.column_widths(length_determining_line))
        column_line = lines[5]

        column_names = self.get_row_data(column_line, column_widths)
        data = []
        for row in lines[7:]:
            if row:
                data.append(self.get_row_data(row, column_widths))
        df = pd.DataFrame(data, columns=column_names)

        df[["Item", "Grp", "Meas", "Cycles", "CntTotGT"]] = (
            df[["Item", "Grp", "Meas", "Cycles", "CntTotGT"]]
            .apply(pd.to_numeric, errors="coerce")
            .astype("Int64")
        )
        df[
            [
                "12Cle",
                "13Cle",
                "12Che",
                "13Che",
                "13/12le",
                "13/12he",
                "14/12he",
                "14/13he",
                "bias",
                "stripPR",
                "FacTR",
            ]
        ] = (
            df[
                [
                    "12Cle",
                    "13Cle",
                    "12Che",
                    "13Che",
                    "13/12le",
                    "13/12he",
                    "14/12he",
                    "14/13he",
                    "bias",
                    "stripPR",
                    "FacTR",
                ]
            ]
            .apply(pd.to_numeric, errors="coerce")
            .astype(float)
        )

        print(df.dtypes)
        print(df)

        return df

    def test_rows(self) -> None:  # ant i6metimo
        lines = self.data.split("\n")
        for row in lines[:30]:
            print("eilute", row)

    def __repr__(self):
        return self.data


if __name__ == "__main__":
    data = Data()
    data.fetch()
    # data.get_column_widths()
    # data.get_column_names()
    data.get_dataframe()
