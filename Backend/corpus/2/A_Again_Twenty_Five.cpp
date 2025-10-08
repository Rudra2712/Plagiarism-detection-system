#include <iostream>
using namespace std;

int main() {
    int x, total = 0;
    cout << "Enter a number: ";
    cin >> x;
    for (int j = 1; j <= x; j++) {
        total = total + j;
    }
    cout << "Sum from 1 to " << x << " = " << total << endl;
    return 0;
}
