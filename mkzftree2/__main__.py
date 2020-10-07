from mkzftree2.arguments import get_options
from mkzftree2.models.FileObject import FileObject, ZISOFS, ZISOFSv2
from mkzftree2.file_process import process_files, find_files


def main(args=None):
    opt = get_options(args)

    source = opt.in_dir[0]
    target = opt.out_dir[0]
    blocksize = opt.blocksize * 2**10

    # Create targer directory
    try:
        target.mkdir(parents=True)
    except FileExistsError: # We already checked that is a empty dir
        pass
    

    # Recursive search of all files
    list_files = find_files(source, opt.file, opt.legacy)

    process_files(list_files, source, target, opt.overwrite, opt.a, opt.z, blocksize)


    # Process
    # d = FileObject.get_smallfiles()
    print("Hola")

if __name__ == '__main__':
    # execute only if run as the entry point into the program
    main()