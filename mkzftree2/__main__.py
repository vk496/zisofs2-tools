from mkzftree2.arguments import get_options
from mkzftree2.file_process import process_files, find_files, uncompress_files


def main(args=None):
    opt = get_options(args)

    source = opt.in_dir[0]
    target = opt.out_dir[0]
    blocksize = 2 ** opt.blocksize

    # Create targer directory
    try:
        target.mkdir(parents=True)
    except FileExistsError:  # We already checked that is a empty dir
        pass

    if opt.uncompress:
        if opt.fuse:
            from mkzftree2.zisofuse import mount_fuse
            print(f"Mounting {source} into {target}")
            mount_fuse(source, target)
        else:
            # Uncompress in_dir
            uncompress_files(source, target)
    else:
        # Compress in_dir

        # Recursive search of all files
        list_files = find_files(source, opt.file, opt.follow_symlinks)

        process_files(list_files, source, target, opt.overwrite, opt.a,
                    opt.z, blocksize, opt.force, opt.legacy, opt.ignore_attributes)

    # Process
    print("\nDone. Have a nice day :)")


if __name__ == '__main__':
    # execute only if run as the entry point into the program
    main()
