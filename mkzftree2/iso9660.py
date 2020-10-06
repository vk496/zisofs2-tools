

def int_to_iso711(value):
    """
    Convert a int to unsigned 1 byte little endian representation
    """
    return value.to_bytes(1, byteorder='little', signed=False)

def iso711_to_int(data):
    """
    Convert a unsigned 1 byte little endian to int representation
    """
    if len(data) != 1:
        raise ValueError(f"{data} size must be 1")

    return int.from_bytes(data, byteorder='little', signed=False)


def int_to_iso731(value):
    """
    Convert a int to unsigned 4 bytes little endian representation
    """
    return value.to_bytes(4, byteorder='little', signed=False)

def iso731_to_int(data):
    """
    Convert a unsigned 4 bytes little endian to int representation
    """
    if len(data) != 4:
        raise ValueError(f"{data} size must be 4")

    return int.from_bytes(data, byteorder='little', signed=False)

def int_to_uint64(value):
    return value.to_bytes(8, byteorder='little', signed=False)

def uint64_to_int(data):
    if len(data) != 8:
        raise ValueError(f"{data} size must be 8")

    return int.from_bytes(data, byteorder='little', signed=False)

def uint64_to_two_iso731(value, one=False):
    """
    Convert a uint64 value to two iso731
    Return first low-order bytes, and after high-order

    With one=True, return it in a single variable
    """
    raw_data = value.to_bytes(8, byteorder='little', signed=False)

    low_order = raw_data[:-4]
    high_order= raw_data[-4:]
    
    if one:
        return bytes(low_order + high_order)
    else:
        return low_order, high_order

def two_iso731_to_uint64(low, high):
    """
    Convert a uint64 value to two iso731
    Return first low-order bytes, and after high-order
    """
    if len(low + high) != 8:
        raise ValueError(f"{low + high} size must be 8")

    return int.from_bytes((low + high), byteorder='little', signed=False)