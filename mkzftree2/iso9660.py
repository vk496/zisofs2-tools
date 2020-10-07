

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
