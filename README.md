JANA QABAJAH TEST TEST

Please copy and paste this in your hookss --->Prepare-commit-msg and delete .sample in the file name


#!/bin/sh
# commit-msg hook for RCS project

HOOK_FILE=$1
COMMIT_MSG=$(head -n1 "$HOOK_FILE")

# تحقق من أن الرسالة تبدأ بـ RCS-<رقم>
if ! echo "$COMMIT_MSG" | grep -Eq "^RCS-[0-9]+"; then
  echo ""
  echo "    ERROR! Bad commit message. "
  echo "    '$COMMIT_MSG' is missing Ticket Number."
  echo "    example: 'RCS-123: my commit'"
  echo ""
  exit 1
fi
