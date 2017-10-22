/*input
5 3

10 5 7

0 1 0
2 0 0
3 0 2
2 1 1
0 0 2

7 5 3
3 2 2
9 0 2
2 2 2
4 3 3

4
3 3 0

1
1 0 2
*/
#include <bits/stdc++.h>

#define matrix_init(mat, m, n, initial_value) mat.resize(m, vi(n, initial_value))
#define matrix_print(mat)  for (auto &row : mat) {  \
                               for (auto &el : row) \
                                  cout << el << " ";\
                               cout << endl;        \
                           }   

#define die(msg)  { cerr << msg << endl; exit(EXIT_FAILURE); }
#define forever   for(;;)

using namespace std;

typedef vector<int> vi;
typedef vector<vi> matrix;

bool is_state_safe(const matrix &state, const matrix &need, vi avail);
bool rsrc_lte(const vi &, const vi &);
template < class Operation> void v_op(vi &, const vi &, Operation);


int main() {
    int    pc      /* Process count                                                      */,
           rc      /* Resource count                                                     */,
           pid     /* Process id for process requesting resources                        */;

    matrix alloc   /* Current allocatin state                                            */, 
           pmax    /* Maximum instances of each resource, needed by processes            */,
           need    /* Further instances of each resources needed to complete the process */;

    vi     request /* Request from process 'pid'                                         */, 
           rlimit  /* Total no of instances of each resources available in system.       */,
           avail   /* No of instances of each resources available  right now             */;

    //cout << "Enter process count & resource count : ";
    cin >> pc >> rc;

    matrix_init(alloc, pc, rc, 0);
    matrix_init(need, pc, rc, 0);
    matrix_init(pmax, pc, rc, 0);
    rlimit.resize(rc, 0);
    avail.resize(rc, 0);
    request.resize(rc, 0);

    //cout << "Enter rlimit of " << rc << " resources : ";
    for (auto &el : rlimit)
        cin >> el;

    //cout << "Enter current allocation matrix : ";
    for (auto &p : alloc)
        for (auto &r : p)
            cin >> r; /* No of instances of r allocated to process p */

    //cout << "Enter PMAX matrix : ";
    for (auto &p : pmax)
        for (auto &r : p)
            cin >> r; /* Max no of instances of resource r required by p to complete the task */


    // Calculate need matrix
    for (int i=0; i< pc; ++i) {
        for (int j=0; j < rc; ++j) {
            need[i][j] = pmax[i][j] - alloc[i][j];
            if (need[i][j] < 0)
                die(string("NEED is -ve for process ") + to_string(i) + string(" & resource = ") + to_string(j));
        }
    }

    //Calculate avail matrix
    for (int r = 0; r < rc; ++r) {
        avail[r] = rlimit[r];
        for (int i=0; i < pc; ++i) {
            avail[r] -= alloc[i][r];
            if(avail[r] < 0)
                die(string("Resource ") + to_string(r) + " is available in -ve no.s!");
        }
    }

    
    if (!is_state_safe(alloc, need, avail)) {
        die("Sorry! System is not in safe state!");
    }

    // Read the incoming request
    cout << "Enter process id : ";
    cin  >> pid;
    cout << "Enter no. of instances of resources requested : ";
    for(auto &el : request)
        cin >> el;

    // Simulate the allocation
    if (! rsrc_lte(request, need[pid]))
        die("Requested too much resources!");
    if (! rsrc_lte(request, avail))
        die("Not enough resources are available!");

    v_op(alloc[pid], request, [](const int &a, const int &b) { return a + b; });
    v_op(need[pid],  request, [](const int &a, const int &b) { return a - b; });
    v_op(avail,      request, [](const int &a, const int &b) { return a - b; });

    if(! is_state_safe(alloc, need, avail)) {
        cout << "The given request cannot be satisfied since it leaves the system in unsafe state." << endl;
        // Rolling back
        v_op(alloc[pid], request, [](const int &a, const int &b) { return a - b; });
        v_op(need[pid],  request, [](const int &a, const int &b) { return a + b; });
        v_op(avail,      request, [](const int &a, const int &b) { return a + b; });
    }
    else {
        cout << "Request successful!" << endl;
    }

    return 0;
}


bool is_state_safe(const matrix &alloc, const matrix &need, vi avail) {
    int m = alloc.size(), n = alloc[0].size();
    assert (m > 0 && m == need.size() && n == need[0].size() && avail.size() == n);
    vector<bool> finished(false, m);
    int pending = m;
    forever {
        bool found = false;
        for(int i=0; i<m ;++i) {
            if (! finished[i] && rsrc_lte(need[i], avail)) {
                v_op (avail, alloc[i], [](const int &a, const int &b) { return a + b; });
                finished[i] = found =  true;
                pending--;
                if(pending == 0) return true;
            } 
        }
        if (!found) return false;
    }
    // Control will never reach here .. 
    return  false;
}

bool rsrc_lte(const vi &r1, const vi &r2) {
    assert (r1.size() > 0 && r1.size() == r2.size());
    for (int i=0; i < r1.size(); ++i) 
        if (r1[i] > r2[i]) return  false;

    return true; 
}

template <class Function>
void v_op(vi &result, const vi &operand, Function func) {
    assert (result.size() > 0 && result.size() == operand.size());
    for (int i=0; i < result.size(); ++i) {
        result[i] = func(result[i], operand[i]);
    }
}n