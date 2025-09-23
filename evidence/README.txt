# Evidence Storage Directory

This directory is used to store acquired forensic images and evidence files.

## Structure
Each case should have its own subdirectory:
- `CASE-001/` - Evidence for case 001
- `CASE-002/` - Evidence for case 002
- etc.

## File Naming Convention
- Use descriptive names: `suspect_laptop_2024-01-15.dd`
- Include acquisition date in filename
- Keep original evidence separate from working copies

## Security Notes
- Ensure evidence integrity with hash verification
- Store original evidence as read-only
- Maintain proper chain of custody documentation
- Use encrypted storage for sensitive cases

## Supported Formats
- Raw disk images (.dd, .raw, .img)
- Expert Witness Format (.E01, .Ex01)
- Advanced Forensics Format (.AFF)
- Memory dumps (.mem, .dmp)
- Virtual machine files (.vmdk, .vdi, .vhd)

## Important
- Never modify original evidence files
- Always work with copies for analysis
- Document all actions in case logs