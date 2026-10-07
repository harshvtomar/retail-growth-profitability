let
    Source = Csv.Document(File.Contents(FolderPath & "FactMonthly.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"month", type text}, {"segment", type text}, {"orders", Int64.Type}, {"returns", Int64.Type}, {"revenue", type number}, {"profit", type number}, {"month_date", type date}}, "en-US")
in
    Typed
