from django.db import models

class AgentPricePerMonth(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Agent Price: ${self.price}/month"

    class Meta:
        verbose_name = "Agent Price Per Month"
        verbose_name_plural = "Agent Price Per Month"


class MinimumTopup(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Minimum Topup: ${self.amount}"

    class Meta:
        verbose_name = "Minimum Topup"
        verbose_name_plural = "Minimum Topup"
        
        
class CallCostPerMinute(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)

    def __str__(self):
        return f"Call Cost: {self.price}"
    
    class Meta:
        verbose_name = "Call Cost Per Minute"
        verbose_name_plural = "Call Cost Per Minute"
