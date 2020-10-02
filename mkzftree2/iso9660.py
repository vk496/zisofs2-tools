

def int_to_iso711(value):
    """
    Convert a int to unsigned 1 byte little endian representation
    """
    return value.to_bytes(1, byteorder='little', signed=False)

def iso711_to_int(data):
    """
    Convert a unsigned 1 byte little endian to int representation
    """
    return int.from_bytes(data, byteorder='little', signed=False) # TODO: limit to 1 byte read


def int_to_iso731(value):
    """
    Convert a int to unsigned 4 bytes little endian representation
    """
    return value.to_bytes(4, byteorder='little', signed=False)

def iso731_to_int(data):
    """
    Convert a unsigned 4 bytes little endian to int representation
    """
    return int.from_bytes(data, byteorder='little', signed=False) # TODO: limit to 4 byte read

def uint64_to_two_iso731(value):
    """
    Convert a uint64 value to two iso731
    Return first low-order bytes, and after high-order
    """
    low_order = int_to_iso731(value & 0xffffffff)
    high_order= int_to_iso731(value >> 32)
    return low_order, high_order

def two_iso731_to_uint64(low, high):
    """
    Convert a uint64 value to two iso731
    Return first low-order bytes, and after high-order
    """
    low_order = iso731_to_int(low)
    high_order= iso731_to_int(high)

    return (high_order << 32 | low_order & 0xffffffff )