mock-pay
========

A mock version of pay.gov for rapid testing

## Setup

This is a Django app that depends on [Python 3](https://docs.python.org/3/).

### Installing Python 3
There are multiple approaches to installing Python 3, depending on your personal setup and preferences.

One option is to [pyenv](https://github.com/yyuu/pyenv) to manage downloading Python 3 or you can install them directly.

For OS X, install Homebrew](http://brew.sh) (OS X), then run `brew install Python3`. For Ubuntu, install using `apt-get install Python3`.


### Project setup

Create an environment to install Python dependencies, with virtualenvwrapper.

```bash
mkvirtualenv --python=/path/to/python3 mockpay
```

Example:
```bash
mkvirtualenv --python=/usr/local/bin/python3 mockpay
```

Note: You don't need to explicitly specify the Python version, especially if
you use pyenv + virtualenvwrapper. Running mkvirtualenv in that scenario will
'freeze' the currently active version of Python.

Pull down the repo:

```bash
git clone https://github.com/18F/mock-pay
cd mock-pay
```

Install project requirements.

```bash
pip install -r requirements.txt
```

### Settings

While the app can be ran out of the box, it won't have any applications to use
(i.e. you will always get a 400 when making requests). To remedy this, create
a `local_settings.py` file inside `mockpay/settings` and include in it
`AGENCY_CONFIG` and `FORM_CONFIGS` variables. See `mockpay/settings/base.py`
for more, but here is an example:

```python
AGENCY_CONFIG= {
    "FBI": {
        "transaction_url": "http://fbi.gov/transaction-default",
        "collection_results_url": "http://fbi.gov/transaction-complete",
        "success_return_url": "http://fbi.gov/happy-path",
        "failure_return_url": "http://fbi.gov/error-path",
        "apps": {
            "FINGERPRINTS": {
                "success_return_url": "http://fbi.gov/fp-success"
            }
        }
    }
}
FORM_CONFIGS = {
    "1111": [{"name": "payer_name", "status": "editable"},
              {"name": "payment_amount", "status": "locked"},
              {"name": "billing_address", "status": "editable"},
              {"name": "billing_city", "status": "editable"},
              {"name": "billing_state", "status": "editable"},
              {"name": "billing_zip", "status": "editable"}]
}
```
