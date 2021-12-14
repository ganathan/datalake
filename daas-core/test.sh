parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
echo $parent_path
if ! echo $parent_path | grep -p "daas-common"; then
    cd ../daas-common
fi

current_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
echo $current_path

echo "now swithching back"
cd $parent_path