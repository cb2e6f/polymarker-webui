import requests

url = 'http://127.0.0.1:5000/snp_files.json'

pm_test_data = {
    "snp_file":
    {
        "reference":"Wheat cv Chinese Spring RefSeq v1.0",
        "email":"rob.ellis@jic.ac.uk"
    },
    "polymarker_manual_input":
    {
        "post": "Cadenza1697.chr1A.12142209,1A,acaacttttcaaaaaataacacacccacaacctaaacacccttaaatatcaacttctgaggggaggcggcaactagtatcaaaaattcaaaatgtggttc[G/C]cacaactagcgttgccgagacaaaaagaaccagcacttccactgctccatgaattcaagaaacagaccgatggcatgtataagaacagacgtgccga\nBA00591935,3B,gcacatcggagagttcgttggaagagcctagcaccgaggaattccaggaggaagatgtctctgatggagattcagactcgaacgacgagagcaaggggcc[G/A]gaagtaaagcttttcatcagcggagtagttcataataaagaggaggctggagcaaaatcttatgttcgagttcccgctgaaataaataacctggaaaggg\nBA00343846,5A,ccacccctcctcttccccatgcagctacaactgaggcaatgctgccgtctgccttctggagttccccgccttcgatctcgagcacgccatccaggacggc[G/A]ttggtatcgaccgccaacctcaatctggatccggttgtggctaatgtacagactaattcccacacaaaacattcattaagttagcattgtctctttttgg\nBA00122841,7D,ttcccaccacacgcttcagcagttccttggctcgcgatgaccccgactcatcatggcagaactgggtccggaggcccccatcaagacccttgtaaatgta[A/G]aagtacactgccagttgttcgctgccgctgttggtggcatggatgagaaggccaaaggggccaagcgcgccgcgttcagtggcaccaccacttgtactgc"
    }
}

r = requests.post(url, json=pm_test_data)
r.raise_for_status()
print(r.json())