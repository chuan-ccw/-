#include <iostream>
#include <vector>
#include <algorithm>
#include <limits>
#include <cmath>

using namespace std;

struct KM {
    int N = 0;
    vector<vector<int>> W;   // 權重矩陣 N x N

    void resize(int n) {
        N = n;
        W.assign(N, vector<int>(N, 0));
        my.assign(N, -1);
        lx.assign(N, 0);
        ly.assign(N, 0);
        vx.assign(N, 0);
        vy.assign(N, 0);
    }

    // 執行 KM 求最大權完備匹配的權重和
    int run() {
        const int INF = numeric_limits<int>::max() / 4;

        // 初始化標號與匹配
        fill(my.begin(), my.end(), -1);
        fill(lx.begin(), lx.end(), numeric_limits<int>::min() / 4);
        fill(ly.begin(), ly.end(), 0);

        // 每一列 lx[i] 取該列最大權
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                lx[i] = max(lx[i], W[i][j]);
            }
        }

        // 對每個左側點做增廣
        for (int i = 0; i < N; ++i) {
            while (true) {
                fill(vx.begin(), vx.end(), 0);
                fill(vy.begin(), vy.end(), 0);
                if (dfs(i)) break;  // 成功增廣

                // 調整標號
                int d = INF;
                for (int x = 0; x < N; ++x) if (vx[x]) {
                    for (int y = 0; y < N; ++y) if (!vy[y]) {
                        d = min(d, lx[x] + ly[y] - W[x][y]);
                    }
                }
                if (d == INF) break; // 沒有可調整的情況（保險）

                for (int x = 0; x < N; ++x) if (vx[x]) lx[x] -= d;
                for (int y = 0; y < N; ++y) if (vy[y]) ly[y] += d;
            }
        }

        // 計算匹配權重和
        int res = 0;
        for (int j = 0; j < N; ++j) {
            if (my[j] != -1) res += W[my[j]][j];
        }
        return res;
    }

private:
    // 右側的匹配 my[j] = 與右點 j 匹配的左點 i
    vector<int> my;
    // 頂點標號
    vector<int> lx, ly;
    // 搜尋時的造訪記號
    vector<int> vx, vy;

    // 等權子圖上的 DFS 增廣
    bool dfs(int u) {
        vx[u] = 1;
        for (int v = 0; v < N; ++v) {
            if (!vy[v] && W[u][v] == lx[u] + ly[v]) {
                vy[v] = 1;
                if (my[v] == -1 || dfs(my[v])) {
                    my[v] = u;
                    return true;
                }
            }
        }
        return false;
    }
};

static inline int manhattan(int x1, int y1, int x2, int y2) {
    return abs(x1 - x2) + abs(y1 - y2);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    KM km;
    int cases = 0;

    int n;
    while ((cin >> n) && n) {
        vector<int> xs(n), ys(n);
        for (int i = 0; i < n; ++i) {
            cin >> xs[i] >> ys[i];
            --xs[i];
            --ys[i];
        }

        km.resize(n);
        const int NEG_INF = numeric_limits<int>::min() / 4;

        int ret = NEG_INF;

        // 1) W[j][k] = -dist( (xs[j], ys[j]) -> (i, k) )
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j)
                for (int k = 0; k < n; ++k)
                    km.W[j][k] = -manhattan(xs[j], ys[j], i, k);
            ret = max(ret, km.run());
        }

        // 2) W[j][k] = -dist( (xs[j], ys[j]) -> (k, i) )
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j)
                for (int k = 0; k < n; ++k)
                    km.W[j][k] = -manhattan(xs[j], ys[j], k, i);
            ret = max(ret, km.run());
        }

        // 3) W[j][i] = -dist( (xs[j], ys[j]) -> (i, i) )
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j)
                km.W[j][i] = -manhattan(xs[j], ys[j], i, i);
        }
        ret = max(ret, km.run());

        // 4) W[j][i] = -dist( (xs[j], ys[j]) -> (i, n-1-i) )
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j)
                km.W[j][i] = -manhattan(xs[j], ys[j], i, n - 1 - i);
        }
        ret = max(ret, km.run());

        cout << "Board " << (++cases) << ": " << (-ret) << " moves required.\n\n";
    }

    return 0;
}

/*


1. vector<int> my;

意義：右側點（目標格）目前配對到哪個左側點（石子）。
my[v] = u 代表右點 v 與左點 u 已匹配；-1 代表還沒匹配。

為什麼要有：

增廣時需要知道「這個右點目前被誰占用」好把路徑沿著匹配邊往回走。

做完後用它計算答案：sum W[ my[v] ][ v ]。

只存右側的匹配就夠了；若要左側的配對，可掃一遍 my 重建。

2. vector<int> vx, vy;（搜尋時的造訪記號）

意義：在單次嘗試增廣（針對某個左點 i）的 DFS 中，標記哪些點已被造訪：

vx[u] = 1：左點 u 已在這次 DFS 走過。

vy[v] = 1：右點 v 已在這次 DFS 走過。

為什麼要有：

避免 DFS 內部重複走訪。

更重要：計算上面的 d（最小鬆弛）時，只考慮 u ? VX、v ? VY 的邊。

3. 在你的程式裡：

W[u][v]：左節點 u（石子）指派到右節點 v（目標格）的權重（你放的是距離取負）。

my 不是右節點本身，而是**「右 → 左」的配對表**：my[v] = u 表示右節點 v 目前配到哪個左節點 u；-1 代表尚未配到。

那「左邊呢」？

這份實作沒有另外存「左 → 右」陣列；


4. 把「W」當成配對的分數表來看，而不是棋盤。

vector<vector<int>> W; 是一個 N×N 的矩陣，在 resize(n) 之後變成 W[n][n]。

這個矩陣不是在存棋盤的 0/1，而是存 “左節點 u = 第 u 顆石子” 和 “右節點 v = 目標線上第 v 個格子” 的配對分數（也叫權重 weight）。

因為 KM 要 最大化權重和，而我們想 最小化總距離，所以把
weight = - (distance)。
這樣「距離越小」→「權重越大（越不負）」→ KM 最大化就等於選最小總距離。

換句話說：

W[u][v] = 這顆石子 u 被指派到目標格 v 時的「分數」。我們定義分數 = 距離取負。

為什麼叫「權重」？

在二分圖指派（Hungarian/KM）裡，每條可配對的邊 (u,v) 都有一個「好不好」的程度，稱作權重（或成本 cost）。

若你是在「最大化」好處（例如收益），就直接把好處當權重。

若你是在「最小化」成本（我們這題是總步數＝總距離），就把
weight = -cost（或 weight = bigConst - cost）轉成最大化問題給 KM。

這個 W 何時被填？

對每一條候選直線（n 條列、n 條行、2 條對角）：

先決定右側的 n 個「目標格」座標（例如固定列 i：右節點 v 對應 (i, v)）。

對每顆石子 u、每個目標格 v，算曼哈頓距離 dist，然後寫入

W[u][v] = -dist;


呼叫 km.run()，得到這條直線的最佳總權重（= -最小總距離）。

所以 W 的內容會「因直線不同而重建」，它是 KM 的輸入分數表，不是棋盤本體。

迷你例子

n=3，挑「固定行 i=1」（直線是 x=1），目標格依序為 (0,1), (1,1), (2,1)。
假設三顆石子在 (0,2)、(1,0)、(2,1)：

| u\→v      | (0,1)           | (1,1)      | (2,1)      |
| --------- | --------------- | ---------- | ---------- |
| u=0 (0,2) | dist=1 ? -1    | 2 ? -2     | 3 ? -3 |
| u=1 (1,0) | 2 ? -2         | 1 ? -1     | 2 ? -2 |
| u=2 (2,1) | 2 ? -2         | 1 ? -1     | 0 ? 0  |

KM 會挑一組配對讓 W[u][v] 總和最大（例如 -1 + -1 + 0 = -2），
等號取負回去就是最小總距離 2 步。

總結：
W 是 指派問題的權重矩陣；元素 W[u][v] 代表把第 u 顆石子指到目標線上的第 v 個格子時的「分數」。
我們把分數定義成 距離的負值，讓 KM 的「最大權匹配」= 我們要的「最小步數」。

所以：W 是分數（權重）矩陣；KM 幫你在「一顆石子對一個目標格」的約束下，挑出加總最好的那組配對。

5. W[u][v]：u = 第 u 顆石子，v = 目標線上的第 v 個格子。值放的是「配對分數」= - 曼哈頓距離。

先固定一條候選直線，把該線上 n 個目標格編成 v=0..n-1，然後把每顆石子 u 到每個格子 v 的距離都算一遍，填進 W[u][v]。

固定第 i 列：目標格是 (i, v)

固定第 i 行：目標格是 (v, i)

主對角線：(v, v)

反對角線：(v, n-1-v)

跑一次 KM，會在「一對一」的限制下，挑出一個排列 π 讓

?u?W[u]?[π(u)]最大（等價於總距離最小）。

取負就是這條直線的最少步數。

對所有列、所有行、兩條對角線都做，最後取最小的步數就是答案。


6. lx[u]：左邊第 u 個點（你這題＝第 u 顆石子）的標號 / 勢能

ly[v]：右邊第 v 個點（你這題＝目標線上第 v 個位置）的標號 / 勢能

它們必須一直滿足可行標號條件：

?u,v: lx[u] + ly[v] ? W[u][v]

而剛好等號的邊（lx[u] + ly[v] == W[u][v]）叫等權邊。
KM 只在「等權邊」上找增廣路；卡住時就微調 lx/ly 去製造新的等權邊。

直覺：lx/ly 像左右兩邊的「抵用券」。一條邊能走，代表左右券加起來剛好「抵到」這條邊的權重；
卡住就動一點券，讓某些快要能走的邊變成剛好能走。

名詞對齊

u：左節點的索引（第 u 顆石子）。例如 u=0 就是「第 0 顆石子」。

v：右節點的索引（目標線上的第 v 個格子）。例如 v=0 就是「第 0 個格子」。

ly[v]：是「右節點 v 的標號（勢能）」，它是一個數值，不是節點本身。v 是索引；ly[v] 是掛在那個索引上的標號值。初始化時 ly[v]=0 只是初值，不是說 v=0。

所以當我說「配 u=0」不是指邊 (0,0)，而是：現在要把左節點 0 配給某個右節點 v（看哪些 v 形成等權邊可以走）。

例子（全部權重不同，和前文一樣）

      9 3 4
?W =   7 5 2   ,lx=[9,7,8], ly=[0,0,0] (初始化)
      1 6 8


等權邊檢查（用規則 lx[u]+ly[v]==W[u][v]）

u=0：
v=0：9+0=9==9 → 等權
v=1：9≠3（非等權），v=2：9≠4（非等權）

u=1：
v=0：7+0=7==7 → 等權
v=1：7≠5，v=2：7≠2（皆非等權）

u=2：
v=2：8+0=8==8 → 等權
v=0：8≠1，v=1：8≠6（皆非等權）

等權邊集合 = {(0,0), (1,0), (2,2)}。
（注意：這裡的 (0,0) 是一條邊 = “左 0 連到 右 0”；不是說「u=0 就等於 (0,0)」。）

「配 u=0」到底做了什麼？

先看 u=0 的等權鄰居有哪些：只有 v=0。

檢查 v=0 現在有沒有人配：my[0] == -1 表示空，所以直接配：my[0]=0。
現在匹配集合 M 有一對：(u0→v0)。

「配 u=1」為何會用到 DFS？

看 u=1 的等權鄰居：只有 v=0。

但 v=0 已被 u=0 佔著（my[0]=0）。想讓 u=1 也能成功，我們就遞迴去問：「那把 v=0 的舊配偶 u=0 換到別的等權右點可以嗎？」
→ 呼叫 dfs(0)。
u=0 的等權鄰居只有 v=0（而 v=0 這輪已經在路徑上了），沒有別的可換 ? dfs(0) 失敗 ? dfs(1) 也失敗。
這就叫找增廣路失敗：目前等權邊太少。

這就是為什麼要用 DFS：
當你想把 u=1 配給 v=0，發現 v=0 被 u=0 佔著，就要沿著匹配邊往回走，看能不能把 u=0 改配其他等權 v'。
這種「走未匹配邊（u→v）、再走匹配邊（v→u'）、再走未匹配邊…」的交替路最方便用 DFS 實作。


最小鬆弛量 d 就是「把等權子圖往外推一點點」所需的最小調整量；
只看 u?VX、v?VY 是因為我們要讓「已探索到的左邊」連到「還沒探索到的右邊」──這樣才可能開出新的等權邊，
DFS 才能繼續。

跑到「配 u=1」時，DFS 失敗；此時

VX（這輪 DFS 造訪到的左點） = {1, 0}

VY（這輪 DFS 造訪到的右點） = {0}

失敗的含義：在等權子圖裡，沒有任何邊從 VX 連到「VY 的外面」。否則 DFS 會繼續走下去，不會停。


等權邊 & slack 全列

可行標號條件：對所有 (u,v) 都要
lx[u] + ly[v] ? W[u][v]。

對每條邊定義 鬆弛量（差多少才變等權）：

slack(u,v) = lx[u]+ly[v]?W[u][v] (?0).


7.   vector<int> xs(n), ys(n)

xs[j]：第 j 顆石子的 x 座標
ys[j]：第 j 顆石子的 y 座標

讀完後 --xs[i]; --ys[i]; 是把輸入的 1-based 轉成 0-based（因為程式內用 0..n-1）。



8. 為什麼用 numeric_limits<int>::min() / 4？

正確性：它比任何可能的 W[i][j] 都小，能正確被 max 覆蓋成「該列最大 W」。

避免整數溢位：KM 之後會算

d = min(lx[x] + ly[y] - W[x][y])

和更新

lx[u] -= d;  ly[v] += d;


為了在最壞情況（例如數值很大）也不會在加減時碰到 INT_MAX/INT_MIN 的溢位，常見習慣是把「哨兵/無窮大」寫成 max()/4、把「極小」寫成 min()/4，預留空間給後續的 ±運算。

std::numeric_limits<int>::min() 大約是 -2,147,483,648；除以 4 變成約 -536,870,912，仍然夠小，但更安全。

同理，你的程式裡也把 INF 寫成 numeric_limits<int>::max() / 4，是同樣的預留頭room習慣。

numeric_limits 是什麼？

來自 <limits> 的模板類，提供型別的極值：

std::numeric_limits<int>::min()：int 可表示的最小值（通常是 -2,147,483,648）

std::numeric_limits<int>::max()：int 可表示的最大值

對整數型別，min() 就是最小（也是 lowest()）；對浮點數 min() 是最小正規格化數，
最小（可能為負）的要用 lowest()。但這裡是 int，用 min()就對了。

9. 為什麼要「/4」？

看這個上界：

∣lx+ly?W∣?∣lx∣+∣ly∣+∣W∣

演算法裡，這三個量都會用到我們的哨兵級別。
若我們把「可用的絕對上界」設為 M，就要讓 3M<INT_MAX才安全。

選 M=INT_MAX/4 ? 3M=3/4 ? INT_MAX<INT_MAX
這樣像 lx + ly - W 這種最壞情況也不會爆 int。

直覺版：之後會做「兩個加法一個減法」，保留到「/4」的量級，就算三個都接近上界，總和也不會超過 int 的極限。

具體數字對比

INT_MAX ? 2,147,483,647

用 /4 之後：M ? 536,870,911

最壞：lx?M, ly?M, -W?M ? lx+ly-W ? 3M ? 1.61e9，還在 int 範圍內。

若用原值 INT_MAX：lx+ly-W 可能到 ~6e9，一定溢位。

10. 對，就是在把每一列的最大值塞進 lx[i]。這段做的事：

for (int i = 0; i < N; ++i) {       // 逐列
    for (int j = 0; j < N; ++j) {   // 掃該列的每個欄
        lx[i] = max(lx[i], W[i][j]);
    }
}

目的

令 lx[i] = max_j W[i][j]，同時 ly[*] = 0，就能保證可行標號：
對所有 j，lx[i] + ly[j] >= W[i][j]（因為 lx[i] 已是那列最大）。

並且每列至少有一條等權邊：在「取到最大值」的那些 j* 上有
lx[i] + ly[j*] == W[i][j*]（因 ly[j*]=0）。這樣 dfs 一開始才「有路可走」。

小例子

若某列 W[i] = {-7, -3, -5}，而 lx[i] 初值是很小的哨兵（如 INT_MIN/4）：

掃 j=0：lx = max(-INF, -7) = -7

掃 j=1：lx = max(-7, -3) = -3

掃 j=2：lx = max(-3, -5) = -3
最後 lx[i] = -3（該列最大），因此 (i, j=1) 成為等權邊。

若一開始把 lx[i] 設 0，而該列全是負數，max(0, 負數) 會一直是 0，取不到真正的列最大，
初始就可能沒有等權邊，KM 會卡住。

11. 這段就是「枚舉一條水平方向的目標線（第 i 列，y=i），把所有石子配到這條列上的 n 個格子」，
並用 KM 算出最小總步數（用負權轉成最大權）。逐行拆給你看：


for (int i = 0; i < n; ++i) {                // 外層：枚舉目標列 y = i
    for (int j = 0; j < n; ++j)              // j = 左邊的節點（第 j 顆石子）
        for (int k = 0; k < n; ++k)          // k = 右邊的節點（第 i 列上的第 k 個格子，座標是 (i, k)）
            km.W[j][k] = -manhattan(xs[j], ys[j], i, k); // 權重 = -距離 = -( |xs[j]-i| + |ys[j]-k| )

    ret = max(ret, km.run());                // 在這條列上做最佳配對，取「負的最小距離和」
}

i：固定一條水平列（y=i）。這時右側的 n 個節點就是這條列上的 n 個格子 (i, 0..n-1)。

j：第 j 顆石子（左側節點），位置是 (xs[j], ys[j])。

k：右側節點的索引，代表該列上的格子 (i, k)。

manhattan(...)：計算石子 j 移動到格子 (i, k) 的曼哈頓距離 |xs[j]-i| + |ys[j]-k|。

為了把「最小化距離總和」丟給 KM（它解的是最大權完備匹配），我們把權重設為 W[j][k] = -距離。
KM 回傳的是「這條列的最大權總和」=「負的最小距離總和」。

ret = max(ret, km.run());：對每一條列都跑一次 KM，
保留最好的那個結果（注意這是最大，因為結果是負值：越接近 0 代表距離總和越小）。
最後整個程式會輸出 -ret，變回正的最小步數。


11.  numeric_limits<int>::min() / 4 是什麼？

std::numeric_limits<T> 是類別模板，專門提供型別 T 的極值與性質。

numeric_limits<int>::min() 是一個靜態成員函式（其實是 static constexpr T min() noexcept），
回傳 int 可表達的最小值（通常是 -2147483648）。

後面的 / 4 只是把這個極小值除以 4，保留「安全緩衝」避免後面做 lx + ly - W 出現整數溢位（你之前已理解 ?）。

注意：這個 min() 跟 std::min(a,b) 完全不是同一個東西！

numeric_limits<T>::min()：無參數、回傳該型別的最小值。

std::min(a,b)（在 <algorithm>）：有參數、回傳兩者中的較小者。

min() 的括號能放東西嗎？格式？

不能。numeric_limits<T>::min() 沒有參數，呼叫格式固定就是：

std::numeric_limits<int>::min()
std::numeric_limits<long long>::min()
// …依型別不同換 T


如果你要比較兩個值誰比較小，才用 std::min(a, b)（這個在 <algorithm>）。

需要 #include <limits> 嗎？

需要。std::numeric_limits 定義在 <limits>。
你的檔案最上面已經有 #include <limits>（做對了）。

額外補充：如果你想用 C 巨集常數也可以 #include <climits>（如 INT_MIN/INT_MAX），
但在泛型與可攜性上，numeric_limits 更推薦。


*/