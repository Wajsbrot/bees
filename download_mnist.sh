#!/usr/bin/env bash

mkdir mnist
cd mnist
curl --header 'Host: kaggle2.blob.core.windows.net' --header 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:41.0) Gecko/20100101 Firefox/41.0' --header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' --header 'Accept-Language: fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3' --header 'DNT: 1' --header 'Referer: https://www.kaggle.com/c/digit-recognizer/data?train.csv' --header 'Connection: keep-alive' 'https://kaggle2.blob.core.windows.net/competitions-data/kaggle/3004/train.csv?sv=2012-02-12&se=2015-10-20T15%3A29%3A39Z&sr=b&sp=r&sig=wIXcH0XLVN%2Foj%2Bsiu6jKk6Yhbfd%2BcFWSIGFz9HRq83Q%3D' -o 'train.csv' -L
curl --header 'Host: kaggle2.blob.core.windows.net' --header 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:41.0) Gecko/20100101 Firefox/41.0' --header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' --header 'Accept-Language: fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3' --header 'DNT: 1' --header 'Referer: https://www.kaggle.com/c/digit-recognizer/data?train.csv' --header 'Connection: keep-alive' 'https://kaggle2.blob.core.windows.net/competitions-data/kaggle/3004/test.csv?sv=2012-02-12&se=2015-10-20T15%3A32%3A17Z&sr=b&sp=r&sig=c7ONkC5P%2BRxUb3fQxcWr7mQ0L436UeY8XHvXcwovlRw%3D' -o 'test.csv' -L