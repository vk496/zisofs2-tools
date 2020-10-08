import os
import platform


def clone_attributes(input_file, output_file):
    """
    Try to clone system attributes from input_file to output_file
    """

    if platform.system() == 'Windows':
        import win32api
        att_i = win32api.GetFileAttributes(str(input_file))
        # Setting att_o to have the same exact attributes as att_i
        win32api.SetFileAttributes(str(output_file), att_i)
    else:
        st = os.stat(input_file)

        try:
            # File owner
            os.chown(output_file, st.st_uid, st.st_gid)
        except Exception as e:
            print(f"Can't copy file owner to {output_file}: {e}")

        try:
            # File permissions
            os.chmod(output_file, st.st_mode)
        except Exception as e:
            print(f"Can't copy file permissions to {output_file}: {e}")

        try:
            # File dates
            os.utime(output_file, times=(st.st_atime, st.st_mtime))
        except Exception as e:
            print(f"Can't copy file date to {output_file}: {e}")



def clone_dir_attributes(input_dir, output_dir):
    """
    Clone recursively directory attributes
    """
    # if not in_dir.is_dir() or not out_dir.is_dir():
    #     raise ValueError("Must be both dirs")

    for in_dir, out_dir in zip(list(reversed(input_dir))[2:], list(reversed(output_dir))[2:]):
        clone_attributes(in_dir, out_dir)

