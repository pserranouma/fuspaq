import math
import requests

# function for reading data from Prometheus
def readDataOpenFaaS(uri, s_data = '', verbose = False):
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

        codes = ['200', '400', '404', '500', '504']

        try:
            result = res['data']['result']
            value_found = None

            for code in codes:
                for item in result:
                    if item['metric']['code'] == code:
                        try:
                            val = float(item['value'][1])
                            if not math.isnan(val):
                                value_found = val
                                break
                        except ValueError:
                            continue
                if value_found is not None:
                    break

            result1 = value_found
            if verbose:
                print(s_data + ": " + str(result1))
        except:
            if verbose: print("Error reading " + s_data)
        return result1, result2


def readData(uri, s_data = '', verbose = False):
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
            result = res['data']['result']
            for item in result:
                mode = item["metric"].get("mode")
                try:
                    val = float(item["value"][1])
                except (ValueError, KeyError):
                    continue

                if mode == "idle":
                    result2 = val
                else:
                    result1 = val
        except:
            if verbose: print("Error reading " + s_data)
        return result1, result2