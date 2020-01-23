from meeshkan.transform.tshark import convert_pcap, transform_tshark
from hamcrest import assert_that, has_length

PCAP_SAMPLE = 'resources/recordings.pcap'

def test_convert_pcap():
    recordings_gen = convert_pcap(PCAP_SAMPLE)
    recordings = list(recordings_gen)
    assert_that(recordings, has_length(168))
