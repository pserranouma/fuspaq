import requests

# function for reading data from Prometheus
def readData(uri, n_values = 1, s_data = '', verbose = False):
    result1 = None
    result2 = None
    rs = None
    try:
        rs = requests.get(uri)
        #if verbose: print(rs.text)
    except:
        if verbose: print("Error: " + s_data + " data not available")
    if rs is not None and rs.status_code == 200:
        res = rs.json()
        try:
            result1 = float(res["data"]["result"][0]["value"][1])
            if n_values == 2: result2 = float(res["data"]["result"][1]["value"][1])
            if verbose:
                print(s_data + ": " + str(result1))
                if n_values == 2: print("i" + s_data + ": " + str(result2))
        except:
            if verbose: print("Error reading " + s_data)
        return result1, result2
