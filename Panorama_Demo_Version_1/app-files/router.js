// router.js - Xử lý định tuyến URL cho Marzipano

// Danh sách các product có sẵn - theo thứ tự trong cây thư mục
var availableProducts = [
  // l1_l1_1_1
  '1a5ab6424adfa1e1',
  
  // l1_l1_2_2
  '0907ced043a892f4',
  '116d8fe1d94b004f',
  
  // l1_l1_3_3
  '2d9dfc066215f1d0',
  '961fab550347f6fa',
  
  // l2_l1_2_2_l2_3_3
  '0013bf73ebe076f7',
  '00334ac8f21d1b5c',
  
  // l2_l1_2_2_l2_4_4
  '0006e253c720cf00',
  '000a87de36f83cca',
  
  // l2_l1_3_3_l2_5_5
  '04172c95a916ac66',
  '05d0fc5832284cff',
  
  // l3_l1_2_2_l2_3_3_l3_5_5
  '0016314bd22c88bf',
  '0020ca9e6b6b5d9d',
  
  // l3_l1_2_2_l2_3_3_l3_7_7
  '000565a39fc5c236',
  '0027992aa5064f2d',
  
  // l3_l1_2_2_l2_4_4_l3_8_8
  '12708b97708d4808',
  '19447476b3764967',
  
  // l4_l1_2_2_l2_3_3_l3_5_5_l4_10_10
  '091ac331c6f2238d',
  '1003664e21e92652'
];

// Hàm này được gọi khi trang web tải xong
function initRouter() {
  // Kiểm tra URL hiện tại
  var path = window.location.pathname;
  
  // Xóa dấu '/' ở đầu và cuối đường dẫn
  var cleanPath = path.replace(/^\/|\/$/g, '');
  
  // Kiểm tra xem đường dẫn có khớp với bất kỳ product nào không
  if (availableProducts.includes(cleanPath)) {
    // Chuyển hướng về trang chính với tham số truy vấn
    window.location.href = '/?product=' + cleanPath;
    return;
  }
  
  // Xử lý tham số truy vấn
  var params = new URLSearchParams(window.location.search);
  var productParam = params.get('product');
  
  if (productParam && availableProducts.includes(productParam)) {
    console.log('Loading product ' + productParam + '...');
    // Đặt product hiện tại vào localStorage để các thành phần khác có thể truy cập
    localStorage.setItem('currentProduct', productParam);
    // Tải file data.js tương ứng
    loadProductData(productParam);
    
    // Cập nhật giá trị trong dropdown selector
    updateProductSelector(productParam);
  } else if (!productParam) {
    // Nếu không có tham số nào, mặc định là product đầu tiên
    var defaultProduct = availableProducts[0];
    localStorage.setItem('currentProduct', defaultProduct);
    loadProductData(defaultProduct);
    
    // Cập nhật giá trị trong dropdown selector
    updateProductSelector(defaultProduct);
  }
  
  // Thiết lập sự kiện cho selector sản phẩm
  setupProductSelector();
}

// Hàm trợ giúp để lấy product key hiện tại
function getCurrentProduct() {
  var params = new URLSearchParams(window.location.search);
  var productParam = params.get('product');
  
  if (productParam && availableProducts.includes(productParam)) {
    return productParam;
  }
  
  // Mặc định trả về product đầu tiên
  return availableProducts[0];
}

// Tải dữ liệu sản phẩm
function loadProductData(productKey) {
  // Nếu đã có script data.js, xóa nó đi
  var existingScript = document.getElementById('product-data-script');
  if (existingScript) {
    existingScript.parentNode.removeChild(existingScript);
  }
  
  // Tạo script mới để tải dữ liệu sản phẩm
  var script = document.createElement('script');
  script.id = 'product-data-script';
  script.src = 'data/' + productKey + '.js';
  script.onload = function() {
    console.log('Loaded data for product ' + productKey);
    // Kích hoạt sự kiện để thông báo cho index.js biết dữ liệu đã được tải
    var event = new CustomEvent('productDataLoaded', { detail: { productKey: productKey } });
    document.dispatchEvent(event);
  };
  script.onerror = function() {
    console.error('Error loading data for product ' + productKey);
    // Fallback to default product if the requested one fails to load
    if (productKey !== availableProducts[0]) {
      loadProductData(availableProducts[0]);
    }
  };
  document.head.appendChild(script);
}

// Cập nhật giá trị selector sản phẩm
function updateProductSelector(productKey) {
  var selector = document.getElementById('productSelector');
  if (selector) {
    selector.value = productKey;
  }
}

// Thiết lập sự kiện cho selector sản phẩm
function setupProductSelector() {
  var selector = document.getElementById('productSelector');
  if (selector) {
    selector.addEventListener('change', function() {
      var selectedProduct = this.value;
      if (selectedProduct) {
        // Cập nhật URL và chuyển hướng
        window.location.href = '/?product=' + selectedProduct;
      }
    });
  }
}

// Khởi tạo router khi DOM đã sẵn sàng
document.addEventListener('DOMContentLoaded', initRouter);
