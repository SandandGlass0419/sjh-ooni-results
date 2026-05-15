import requests
import csv
from datetime import datetime, timedelta, timezone

global OUT_DIR  # individual reports, stats are outputed here
OUT_DIR = r""
global ID_LIST_PATH # set path for list of report_id
ID_LIST_PATH = r""

def main():   
    for (report_id, expected) in get_report_id_list(ID_LIST_PATH):
        oonitool = OONIExport(report_id, expected, OUT_DIR)
        oonitool.export_data_csv()

def get_report_id_list(report_id_list_path):
    report_id_list = []

    with open(report_id_list_path, newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
    
        for row in reader:
            report_id_list.append((row[0], int(row[1]))) # report_id, expected_count
            
    return report_id_list
    
class OONIExport:
    def __init__(self, report_id, expected_count, out_dir):
        self.report_id = report_id
        self.expected_count = expected_count
        self.out_dir = out_dir
        
        self.id_whole = self.fetch_json(self.get_url_id(report_id)) # results searched using report_id
        self.diff_list = self.get_diff_list()   # results searched using time(test start ~ test end) - id_whole
        self.valid_diff_list = []   # filtered diff_list, only has results from report_id
        
        self.stats = Results()
        self.export_data = []

# api url to get using report_id
    def get_url_id(self, report_id):
        return f"https://api.ooni.io/api/v1/measurements?test_name=web_connectivity&probe_cc=KR&probe_asn=AS3786&order=asc&limit=3000&report_id={report_id}"
        
# api url to get using time
# test start/end is from id_whole first/last element time
# make sure the last test result is included on id_whole
    def get_url_time(self):
        start_str = self.id_whole.get("results")[0].get("measurement_start_time")     
        start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%S.000000Z").replace(tzinfo=timezone.utc)
        start = start - timedelta(seconds=1)    # -1 sec to include first result
        start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        end_str = self.id_whole.get("results")[-1].get("measurement_start_time")
        end = datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%S.000000Z").replace(tzinfo=timezone.utc)
        end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return f"https://api.ooni.io/api/v1/measurements?test_name=web_connectivity&probe_cc=KR&probe_asn=AS3786&order=asc&limit=3000&since={start_str}&until={end_str}"
        
    def get_explorer_url(self, entry):
        return f"https://explorer.ooni.org/m/{entry.get("measurement_uid")}"        
        
    def fetch_json(self, url):
        r = requests.get(url)
        if "application/json" not in r.headers.get("Content-Type",""):
            raise Exception(f"Request got code: {r.status_code}, '{r.text}'")
            
        return r.json()
        
    def fetch_measurement(self, entry):
        url = entry.get("measurement_url")
        return self.fetch_json(url)        
        
# diff_list = time results - id results    
    def get_diff_list(self):
        time_whole = self.fetch_json(self.get_url_time())
        time_count = time_whole.get("metadata").get("count")
        id_count = self.id_whole.get("metadata").get("count")
        
        print(f"{self.report_id}")
        print(f"id: {id_count}, time: {time_count}, expected: {self.expected_count}")
        
        if id_count == self.expected_count: # diff is empty if id_whole has all expected results
            return []
        
        if not id_count <= self.expected_count <= time_count:   # time_count = id_count + results from other tests(that ran on same time)
            print("Something is wrong!, check expected_count or time. (or some results may not be uploaded)")
            
        return [x for x in time_whole.get("results") if x.get("report_id") != self.report_id]
        
# filter diff_list using "test_start_time" in measurement    
    def filter_diff_list(self, test_start_time):            
        filtered = []
        
        for entry in self.diff_list:
            measurement = self.fetch_measurement(entry)
            
            if measurement.get("test_start_time") == test_start_time:
                filtered.append(entry)
                
        print(f"Filtering found {len(filtered)} new entries.")       
                
        return filtered

# write indivisual results, append stat data to stats.csv
    def export_data_csv(self):
        self.update_export_data()
        
        print(f"Exporting {len(self.export_data)} entries.")
        
        report_path = self.out_dir + self.report_id + ".csv"
        with open(report_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            
            for entry in self.export_data:
                writer.writerow(entry)
        
            writer.writerow(self.stats.names)
            writer.writerow(self.stats.count)
            writer.writerow([f"{len(self.export_data)}/{self.expected_count} (expected)"])
            
        stats_path = self.out_dir + "stats.csv"   
        with open(stats_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            
            row = [self.report_id]
            row.extend(self.stats.count)
            writer.writerow(row)
            
# clear, update export_data            
    def update_export_data(self):
        self.export_data.clear()
        
        measurement = self.fetch_measurement(self.id_whole.get("results")[0])
        test_start_time = measurement.get("test_start_time")    # get test_start_time from element in id_whole
        
        self.valid_diff_list = self.filter_diff_list(test_start_time)
        
        self.append_export_data(self.id_whole.get("results"))   # add results from id_whole
        self.append_export_data(self.valid_diff_list)   # add results from filtered diff

        self.stats.count[self.stats.NO_DATA] += self.expected_count - len(self.export_data) # add failed amount
        
# add list of result to export_data        
    def append_export_data(self, results):
        for entry in results:
            data = []
            
            result = self.get_result(entry)
            
            data.append(entry.get("input")) # test site url
            data.append(self.stats.get_name(result))
            data.append(self.get_explorer_url(entry))   # ooni explorer link to view measurement data(test_keys)
    
            self.stats.increment(result)
                
            self.export_data.append(data)             
            
# get result from json entry        
    def get_result(self, entry):
        if entry.get("failure"):
            return self.stats.ERROR
        if entry.get("confirmed"):
            return self.stats.CONFIRM
        if not entry.get("anomaly"):
            return self.stats.OK
            
        blocking = entry.get("scores").get("analysis", None).get("blocking_type", None)
                    
        if blocking is None:
            return self.stats.NO_DATA
        if blocking == "dns":
            return self.stats.DNS
        if blocking == "tcp_ip":
            return self.stats.TCP_IP            
        if blocking == "http-diff":
            return self.stats.HTTP_DIFF
        if blocking == "http-failure":
            return self.stats.HTTP_FAIL
        if blocking == "http":
            return self.stats.HTTP
        else:
            print(blocking)
            return stats.NO_DATA
        
# get more data from measurement
# currently not used (takes too long to get measurement data for each test url)
    def dns_block_data(self, test_keys):     
        data = []
        
        data.append(str(test_keys.get("dns_experiment_failure")))
        data.append(str(test_keys.get("dns_consistancy")))
        
        return data
        
    def tcp_ip_block_data(self, test_keys):
        data = []
        
        for element in test_keys.get("tcp_connect"):
           if not element.get("status").get("blocked"): # only write unblocked ones
               data.append(f"{element.get("ip")}:{element.get("port")}")
               
        return data
       
    def http_block_data(self, test_keys):
        data = []
        
        data.append(str(test_keys.get("http_experiment_failure")))
        data.append(str(test_keys.get("status_code_match")))
        data.append(str(test_keys.get("headers_match")))
        data.append(str(test_keys.get("body_length_match")))
        data.append(str(test_keys.get("title_match")))
        
        return data
        
    def experiment_data(self, test_keys):
        data = []
        
        data.append(str(test_keys.get("dns_experiment_failure")))
        data.append(str(test_keys.get("http_experiment_failure")))
        data.append(str(test_keys.get("control_failure")))
        
        return data

class Results:
    def __init__(self):
        self.OK = 0
        self.DNS = 1
        self.TCP_IP = 2
        self.HTTP_DIFF = 3  # http reponse different from control(ooni test server)
        self.HTTP_FAIL = 4  # can't establish http connection
        self.CONFIRM = 5    # blockpage is served(like warning.gov)
        self.ERROR = 6  # ooni experiment failed
        self.NO_DATA = 7 # when failed to get data (when this tool failed to find result or found data doesn't contain result)
        self.HTTP = 8 # legacy
        
        self.names = ["ok", "dns", "tcp_ip", "http-diff", "http-failure", "confirmed", "error", "no_data", "http(legacy)"]
        self.count = [0] * 9
        
    def increment(self, result_type):
        self.count[result_type] += 1
        
    def get_index(self, name):
        return self.names.index(name)
        
    def get_name(self, index):
        return self.names[index]    
        
if __name__ == "__main__":
    main() 