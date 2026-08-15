NEW=0b3e4d6c216f82df7e3d29dd167a58b9e2d7d996c03c1fb0d44c1c63bc0df454
OLD=98f3f429a0110f72cac473b018d17e114236b1a5c4302418d2c0cd039a8a2d85
for f in .github/workflows/tests-linux.yml .github/workflows/tests-windows.yml; do
  n=$(grep -c "$OLD" "$f"); [ "$n" = "1" ] || { echo "STOP: $f has $n"; break; }
  sed -i "s/$OLD/$NEW/" "$f"; echo "updated $f"
done
