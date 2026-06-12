# Windows CI Blocker After Version Resolution v0.1

## Evidence

- Historical run `27336481022`: Ubuntu passed; Windows failed at `Run tests`.
- One reported failure is confirmed `path_separator_related` and is fixed by POSIX serialization.
- The local strict-doctor failure was `generated_file_related` and `dirty_worktree_related`: staged `papers.db` caused aggregate code 1 while timezone remained healthy.
- The authenticated Windows job log is unavailable, so the exact remote cause of its doctor assertion remains `unresolved`.

## Status

The corrective patch passes repository-scoped tests locally on Windows Python 3.15.0b2. Windows CI must still be rerun after publication. Ubuntu remains historically green.
