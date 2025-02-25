import requests

url = 'http://127.0.0.1:5000/echo'
dat = { 'lang': 'python' }

pm_test_data = {
    "snp_file":
    {
        "reference":"RefSeq v1.0",
        "email":""
    },
    "polymarker_manual_input":
    {
        "post":"1DS_1905169_Cadenza0423_2404_C2404T,1D,ccgccgtcgtatggagcaggccggccaattccttcaaggagtcaaccacctggcgcaaggaccatgaggtccatgctcacgaggtctctttcgttgacgg[C/T]aaaaacaagacggcgccaggctttgagttgctcccggctgtggtggatcaccaaggcaacccgcagccgaccttggtggggatccacgttggccatcccaa\n1DS_40060_Cadenza0423_2998_G2998A,1D,ccagcagcgcccgtcccccttctcccccgaatccgccggagcccagcggacgccggccatgagcacctccgagtagtaagtccccggcgccgccgccgcc[G/A]ccgatctttctttctttctcgcttgatttgtctgcgtttcttttgttccgggtgattgattgatgtgcgtgggctgctgcagcgactacctcttcaagctg\n1DS_1847781_Cadenza0423_2703_G2703A,1D,tttcctctcaaatgtagcttctgcagattcggtggaagggcattcaaccggagaacctcattctcatcacttgcggtcacctctaggtaggacaaaaact[G/A]catctgaataagagactcacagaggcgttcacagtagattctcttcacattcaataacctcaggcttctcatttgcctcagctctcccagttgtctaacag"
    }
}

r = requests.post(url, json=pm_test_data)
r.raise_for_status()
print(r.json())