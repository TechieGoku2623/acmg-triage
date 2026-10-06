#!/usr/bin/env bash
set +e
acmg classify --hgvs "NM_000059.4:c.2311G>A" --summary
exit $?
